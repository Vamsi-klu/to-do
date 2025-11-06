from __future__ import annotations

import os
from functools import wraps
from typing import Any, Dict

from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from openai import OpenAI

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, environment variables must be set manually

from database import db, init_db
from models import User, Todo


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    # Basic config
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", os.urandom(24)),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///db.sqlite3"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JSON_SORT_KEYS=False,
    )

    init_db(app)
    register_routes(app)
    return app


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def get_current_user() -> User | None:
    uid = session.get("user_id")
    if not uid:
        return None
    return db.session.get(User, uid)


def register_routes(app: Flask) -> None:
    @app.get("/")
    @login_required
    def index():
        user = get_current_user()
        return render_template("index.html", user=user)

    @app.get("/login")
    def login():
        if session.get("user_id"):
            return redirect(url_for("index"))
        return render_template("login.html")

    @app.post("/login")
    def login_post():
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return render_template("login.html", error="Invalid credentials. Please try again."), 401
        session["user_id"] = user.id
        return redirect(url_for("index"))

    @app.get("/register")
    def register():
        if session.get("user_id"):
            return redirect(url_for("index"))
        return render_template("register.html")

    @app.post("/register")
    def register_post():
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not username or not password:
            return render_template("register.html", error="Username and password are required."), 400
        if password != confirm:
            return render_template("register.html", error="Passwords do not match."), 400
        if User.query.filter_by(username=username).first():
            return render_template("register.html", error="Username already exists."), 400

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        return redirect(url_for("index"))

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    # ---- API endpoints ----
    @app.get("/api/todos")
    @login_required
    def api_list_todos():
        user = get_current_user()
        todos = (
            Todo.query.filter_by(user_id=user.id)
            .order_by(Todo.created_at.desc())
            .all()
        )
        return jsonify([serialize_todo(t) for t in todos])

    @app.post("/api/todos")
    @login_required
    def api_create_todo():
        user = get_current_user()
        payload: Dict[str, Any] = request.get_json(force=True, silent=True) or {}
        text = (payload.get("text") or "").strip()
        if not text:
            return jsonify({"error": "Text is required"}), 400
        todo = Todo(user_id=user.id, text=text, completed=False)
        db.session.add(todo)
        db.session.commit()
        return jsonify(serialize_todo(todo)), 201

    @app.patch("/api/todos/<int:todo_id>")
    @login_required
    def api_update_todo(todo_id: int):
        user = get_current_user()
        todo = Todo.query.filter_by(id=todo_id, user_id=user.id).first()
        if not todo:
            abort(404)
        payload: Dict[str, Any] = request.get_json(force=True, silent=True) or {}
        if "text" in payload:
            text = (payload.get("text") or "").strip()
            if not text:
                return jsonify({"error": "Text is required"}), 400
            todo.text = text
        if "completed" in payload:
            todo.completed = bool(payload["completed"])
        db.session.commit()
        return jsonify(serialize_todo(todo))

    @app.delete("/api/todos/<int:todo_id>")
    @login_required
    def api_delete_todo(todo_id: int):
        user = get_current_user()
        todo = Todo.query.filter_by(id=todo_id, user_id=user.id).first()
        if not todo:
            abort(404)
        db.session.delete(todo)
        db.session.commit()
        return ("", 204)

    # ---- AI endpoints ----
    @app.post("/api/ai/summary")
    @login_required
    def api_ai_summary():
        user = get_current_user()
        todos = (
            Todo.query.filter_by(user_id=user.id)
            .order_by(Todo.created_at.desc())
            .all()
        )

        if not todos:
            return jsonify({"summary": "You don't have any tasks yet. Start by adding some tasks to get organized!"}), 200

        # Get OpenAI API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return jsonify({"error": "OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable."}), 500

        try:
            client = OpenAI(api_key=api_key)

            # Format tasks for the AI
            completed_tasks = [t for t in todos if t.completed]
            active_tasks = [t for t in todos if not t.completed]

            task_text = f"""You have {len(todos)} total tasks:
- {len(completed_tasks)} completed tasks
- {len(active_tasks)} active tasks

Active tasks:
"""
            for t in active_tasks[:10]:  # Limit to 10 tasks
                task_text += f"- {t.text}\n"

            if len(active_tasks) > 10:
                task_text += f"... and {len(active_tasks) - 10} more\n"

            task_text += "\nCompleted tasks:\n"
            for t in completed_tasks[:5]:  # Limit to 5 completed
                task_text += f"- {t.text}\n"

            if len(completed_tasks) > 5:
                task_text += f"... and {len(completed_tasks) - 5} more\n"

            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes task lists. Provide a brief, encouraging summary of the user's tasks, highlighting what they've accomplished and what's next."},
                    {"role": "user", "content": f"Please summarize my tasks:\n\n{task_text}"}
                ],
                max_tokens=200,
                temperature=0.7
            )

            summary = response.choices[0].message.content.strip()
            return jsonify({"summary": summary}), 200

        except Exception as e:
            return jsonify({"error": f"Failed to generate summary: {str(e)}"}), 500

    @app.post("/api/ai/suggestions")
    @login_required
    def api_ai_suggestions():
        user = get_current_user()
        todos = (
            Todo.query.filter_by(user_id=user.id)
            .order_by(Todo.created_at.desc())
            .all()
        )

        # Get OpenAI API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return jsonify({"error": "OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable."}), 500

        try:
            client = OpenAI(api_key=api_key)

            # Format tasks for the AI
            if todos:
                task_text = "Based on these existing tasks:\n"
                for t in todos[:15]:  # Limit to 15 tasks
                    status = "✓" if t.completed else "○"
                    task_text += f"{status} {t.text}\n"

                if len(todos) > 15:
                    task_text += f"... and {len(todos) - 15} more\n"
            else:
                task_text = "The user has no tasks yet.\n"

            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that suggests new tasks based on existing ones. Provide 3-5 relevant, actionable task suggestions. Keep them concise and practical."},
                    {"role": "user", "content": f"{task_text}\n\nPlease suggest some relevant new tasks I could add to my list."}
                ],
                max_tokens=250,
                temperature=0.8
            )

            suggestions = response.choices[0].message.content.strip()
            return jsonify({"suggestions": suggestions}), 200

        except Exception as e:
            return jsonify({"error": f"Failed to generate suggestions: {str(e)}"}), 500


def serialize_todo(todo: Todo) -> dict[str, Any]:
    return {
        "id": todo.id,
        "text": todo.text,
        "completed": todo.completed,
        "created_at": todo.created_at.isoformat(),
        "updated_at": todo.updated_at.isoformat() if todo.updated_at else None,
    }


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

