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
from datetime import datetime, timedelta
import re


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
        notes = (payload.get("notes") or "").strip()
        progress = payload.get("progress", 0)
        todo = Todo(user_id=user.id, text=text, notes=notes, progress=progress, completed=False)
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
        if "notes" in payload:
            todo.notes = (payload.get("notes") or "").strip()
        if "progress" in payload:
            progress = int(payload.get("progress", 0))
            todo.progress = max(0, min(100, progress))  # Clamp between 0-100
        if "completed" in payload:
            todo.completed = bool(payload["completed"])
            # Auto-set progress to 100 when completed
            if todo.completed and todo.progress < 100:
                todo.progress = 100
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

    @app.get("/api/todos/<int:todo_id>/ai-summary")
    @login_required
    def api_todo_ai_summary(todo_id: int):
        user = get_current_user()
        todo = Todo.query.filter_by(id=todo_id, user_id=user.id).first()
        if not todo:
            abort(404)

        summary = generate_ai_summary(todo, user)
        return jsonify(summary)


def serialize_todo(todo: Todo) -> dict[str, Any]:
    return {
        "id": todo.id,
        "text": todo.text,
        "notes": todo.notes,
        "progress": todo.progress,
        "completed": todo.completed,
        "created_at": todo.created_at.isoformat(),
        "updated_at": todo.updated_at.isoformat() if todo.updated_at else None,
    }


def generate_ai_summary(todo: Todo, user: User) -> dict[str, Any]:
    """Generate AI-powered summary and suggestions for a task."""

    # Calculate time-based insights
    now = datetime.utcnow()
    created_days = (now - todo.created_at).days
    if todo.updated_at:
        updated_hours = (now - todo.updated_at).total_seconds() / 3600
    else:
        updated_hours = (now - todo.created_at).total_seconds() / 3600

    # Analyze task text for keywords and patterns
    text_lower = todo.text.lower()
    notes_lower = (todo.notes or "").lower()
    combined_text = f"{text_lower} {notes_lower}"

    # Generate smart summary
    summary_parts = []

    # Status summary
    if todo.completed:
        summary_parts.append(f"✅ Task completed! Great job on finishing this task.")
    elif todo.progress >= 75:
        summary_parts.append(f"🚀 Almost there! You're {todo.progress}% done with this task.")
    elif todo.progress >= 50:
        summary_parts.append(f"💪 You're halfway through! Keep up the momentum.")
    elif todo.progress >= 25:
        summary_parts.append(f"📈 Making progress! You've completed {todo.progress}% so far.")
    elif todo.progress > 0:
        summary_parts.append(f"🎯 Just getting started. You're at {todo.progress}% progress.")
    else:
        summary_parts.append("📋 This task is ready to begin.")

    # Time-based insights
    if created_days == 0:
        summary_parts.append("Created today.")
    elif created_days == 1:
        summary_parts.append("Created yesterday.")
    elif created_days <= 7:
        summary_parts.append(f"Created {created_days} days ago.")
    elif created_days <= 30:
        weeks = created_days // 7
        summary_parts.append(f"Created {weeks} week{'s' if weeks > 1 else ''} ago.")
    else:
        months = created_days // 30
        summary_parts.append(f"Created {months} month{'s' if months > 1 else ''} ago.")

    if updated_hours < 1:
        summary_parts.append("Recently updated.")
    elif updated_hours < 24:
        summary_parts.append(f"Last updated {int(updated_hours)} hour{'s' if updated_hours > 1 else ''} ago.")
    elif updated_hours < 168:
        days = int(updated_hours / 24)
        summary_parts.append(f"Last updated {days} day{'s' if days > 1 else ''} ago.")

    # Generate AI suggestions based on task content
    suggestions = []

    # Priority-based suggestions
    if any(word in combined_text for word in ["urgent", "asap", "important", "critical", "priority"]):
        suggestions.append({
            "icon": "🔥",
            "type": "priority",
            "text": "This task appears to be high priority. Consider working on it soon."
        })

    # Meeting/call suggestions
    if any(word in combined_text for word in ["meeting", "call", "zoom", "teams", "conference"]):
        suggestions.append({
            "icon": "📞",
            "type": "meeting",
            "text": "Schedule this meeting in your calendar and send invites to participants."
        })

    # Email suggestions
    if any(word in combined_text for word in ["email", "send", "reply", "respond"]):
        suggestions.append({
            "icon": "📧",
            "type": "email",
            "text": "Draft this email in advance to save time when you're ready to send."
        })

    # Research/learning suggestions
    if any(word in combined_text for word in ["research", "learn", "study", "read", "course"]):
        suggestions.append({
            "icon": "📚",
            "type": "learning",
            "text": "Break this learning task into smaller chunks for better retention."
        })

    # Shopping/buying suggestions
    if any(word in combined_text for word in ["buy", "purchase", "shop", "order", "groceries"]):
        suggestions.append({
            "icon": "🛒",
            "type": "shopping",
            "text": "Make a list of items to avoid forgetting anything important."
        })

    # Planning suggestions
    if any(word in combined_text for word in ["plan", "organize", "prepare", "schedule"]):
        suggestions.append({
            "icon": "📅",
            "type": "planning",
            "text": "Create a timeline with specific milestones for better organization."
        })

    # Writing suggestions
    if any(word in combined_text for word in ["write", "document", "report", "article", "blog"]):
        suggestions.append({
            "icon": "✍️",
            "type": "writing",
            "text": "Start with an outline to structure your thoughts before writing."
        })

    # Review suggestions
    if any(word in combined_text for word in ["review", "check", "verify", "test", "qa"]):
        suggestions.append({
            "icon": "🔍",
            "type": "review",
            "text": "Create a checklist to ensure thorough review of all aspects."
        })

    # Long-running task suggestions
    if created_days > 7 and not todo.completed and todo.progress < 50:
        suggestions.append({
            "icon": "⏰",
            "type": "reminder",
            "text": "This task has been pending for a while. Consider breaking it into smaller sub-tasks."
        })

    # Near completion suggestions
    if todo.progress >= 80 and not todo.completed:
        suggestions.append({
            "icon": "🏁",
            "type": "completion",
            "text": "You're almost done! Schedule time to finish this task soon."
        })

    # Stale task suggestions
    if updated_hours > 168 and not todo.completed:  # Not updated in a week
        suggestions.append({
            "icon": "💤",
            "type": "stale",
            "text": "This task hasn't been updated recently. Is it still relevant?"
        })

    # General productivity suggestions
    if not suggestions:
        suggestions.append({
            "icon": "💡",
            "type": "general",
            "text": "Break this task into smaller steps to make progress easier to track."
        })
        suggestions.append({
            "icon": "🎯",
            "type": "general",
            "text": "Set a specific deadline to create accountability and urgency."
        })

    # Generate insights
    insights = []

    # Progress insights
    if todo.progress > 0 and not todo.completed:
        days_since_update = updated_hours / 24
        if days_since_update > 0:
            velocity = todo.progress / max(1, created_days)
            if velocity > 0:
                days_to_complete = (100 - todo.progress) / velocity
                if days_to_complete < 7:
                    insights.append(f"At your current pace, you could complete this in about {int(days_to_complete)} days.")

    # Consistency insights
    if created_days > 0 and not todo.completed:
        if updated_hours < 24:
            insights.append("You're actively working on this task. Great consistency!")
        elif updated_hours > 72:
            insights.append("Consider dedicating some time to this task to maintain momentum.")

    return {
        "summary": " ".join(summary_parts),
        "suggestions": suggestions[:4],  # Limit to top 4 suggestions
        "insights": insights,
        "stats": {
            "days_since_created": created_days,
            "hours_since_updated": round(updated_hours, 1),
            "progress_percentage": todo.progress,
            "is_completed": todo.completed,
        }
    }


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

