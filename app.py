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

