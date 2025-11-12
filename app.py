from __future__ import annotations

import os
import logging
from functools import wraps
from typing import Any, Dict
from datetime import datetime

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
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from pythonjsonlogger import jsonlogger

from config import get_config
from database import db, init_db
from models import User, Todo
from validators import (
    validate_username,
    validate_password,
    validate_todo_text,
    validate_priority,
    validate_category,
    sanitize_string,
)

# Load environment variables
load_dotenv()


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure Flask application.

    Args:
        config_name: Configuration environment name

    Returns:
        Configured Flask application
    """
    app = Flask(__name__, instance_relative_config=False)

    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Initialize extensions
    init_db(app)
    csrf = CSRFProtect(app)

    # Initialize rate limiter (disable if RATELIMIT_ENABLED is False)
    # Store as app attribute to prevent garbage collection
    app.limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"] if app.config.get("RATELIMIT_ENABLED", True) else [],
        storage_uri=app.config.get("RATELIMIT_STORAGE_URL", "memory://"),
        enabled=app.config.get("RATELIMIT_ENABLED", True),
    )

    # Setup logging
    setup_logging(app)

    # Register routes
    register_routes(app, app.limiter, csrf)

    # Register error handlers
    register_error_handlers(app)

    app.logger.info("Application started successfully")
    return app


def setup_logging(app: Flask) -> None:
    """Configure application logging.

    Args:
        app: Flask application instance
    """
    if not app.debug:
        # Create logs directory if it doesn't exist
        if not os.path.exists("logs"):
            os.mkdir("logs")

        # File handler with JSON formatting
        file_handler = logging.FileHandler("logs/app.log")
        file_handler.setLevel(logging.INFO)

        # JSON formatter for structured logging
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s"
        )
        file_handler.setFormatter(formatter)

        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)


def login_required(view):
    """Decorator to require authentication for routes.

    Args:
        view: View function to wrap

    Returns:
        Wrapped view function
    """
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            # Return JSON error for API endpoints
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("login"))

        # Verify user exists (prevent forged sessions)
        user = db.session.get(User, user_id)
        if not user:
            session.clear()
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Invalid session"}), 401
            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped


def get_current_user() -> User | None:
    """Get currently authenticated user.

    Returns:
        User object if authenticated, None otherwise
    """
    uid = session.get("user_id")
    if not uid:
        return None
    return db.session.get(User, uid)


def register_routes(app: Flask, limiter: Limiter, csrf: CSRFProtect) -> None:
    """Register all application routes.

    Args:
        app: Flask application instance
        limiter: Rate limiter instance
        csrf: CSRF protection instance
    """

    # ---- Page Routes ----

    @app.get("/")
    @login_required
    def index():
        """Main todo list page."""
        user = get_current_user()
        return render_template("index.html", user=user)

    @app.get("/login")
    def login():
        """Login page."""
        if session.get("user_id"):
            return redirect(url_for("index"))
        return render_template("login.html")

    @app.post("/login")
    @limiter.limit("5 per minute")
    def login_post():
        """Process login form."""
        username = sanitize_string(request.form.get("username", ""))
        password = request.form.get("password", "")

        if not username or not password:
            app.logger.warning(f"Login attempt with missing credentials from {request.remote_addr}")
            return render_template("login.html", error="Username and password are required."), 400

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            app.logger.warning(f"Failed login attempt for username: {username} from {request.remote_addr}")
            return render_template("login.html", error="Invalid credentials. Please try again."), 401

        session["user_id"] = user.id
        app.logger.info(f"User {username} logged in successfully")
        return redirect(url_for("index"))

    @app.get("/register")
    def register():
        """Registration page."""
        if session.get("user_id"):
            return redirect(url_for("index"))
        return render_template("register.html")

    @app.post("/register")
    @limiter.limit("3 per hour")
    def register_post():
        """Process registration form."""
        username = sanitize_string(request.form.get("username", ""))
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        # Validate username
        is_valid, error = validate_username(username)
        if not is_valid:
            return render_template("register.html", error=error), 400

        # Validate password
        is_valid, error = validate_password(password)
        if not is_valid:
            return render_template("register.html", error=error), 400

        # Check password confirmation
        if password != confirm:
            return render_template("register.html", error="Passwords do not match."), 400

        # Check if username exists
        if User.query.filter_by(username=username).first():
            app.logger.warning(f"Registration attempt with existing username: {username}")
            return render_template("register.html", error="Username already exists."), 400

        # Create user
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        app.logger.info(f"New user registered: {username}")
        session["user_id"] = user.id
        return redirect(url_for("index"))

    @app.post("/logout")
    @login_required
    def logout():
        """Logout user."""
        username = get_current_user().username if get_current_user() else "Unknown"
        session.clear()
        app.logger.info(f"User {username} logged out")
        return redirect(url_for("login"))

    # ---- API Endpoints ----

    @app.get("/api/todos")
    @login_required
    @limiter.limit("100 per minute")
    def api_list_todos():
        """List all todos for current user with optional filtering and pagination."""
        user = get_current_user()

        # Get query parameters
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 50, type=int), 100)  # Max 100
        filter_status = request.args.get("status")  # all, active, completed
        search = request.args.get("search", "").strip()
        priority = request.args.get("priority")
        category = request.args.get("category")

        # Build query
        query = Todo.query.filter_by(user_id=user.id)

        # Apply filters
        if filter_status == "active":
            query = query.filter_by(completed=False)
        elif filter_status == "completed":
            query = query.filter_by(completed=True)

        if search:
            query = query.filter(Todo.text.ilike(f"%{search}%"))

        if priority:
            query = query.filter_by(priority=priority)

        if category:
            query = query.filter_by(category=category)

        # Order by created_at descending
        query = query.order_by(Todo.created_at.desc())

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            "todos": [serialize_todo(t) for t in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page,
            "per_page": per_page,
        })

    @app.post("/api/todos")
    @login_required
    @limiter.limit("30 per minute")
    def api_create_todo():
        """Create a new todo."""
        user = get_current_user()
        payload: Dict[str, Any] = request.get_json(force=True, silent=True) or {}

        # Validate text
        text = sanitize_string(payload.get("text", ""))
        is_valid, error = validate_todo_text(text)
        if not is_valid:
            return jsonify({"error": error}), 400

        # Validate priority (optional)
        priority = payload.get("priority", "medium")
        is_valid, error = validate_priority(priority)
        if not is_valid:
            return jsonify({"error": error}), 400

        # Validate category (optional)
        category = sanitize_string(payload.get("category", ""))
        is_valid, error = validate_category(category)
        if not is_valid:
            return jsonify({"error": error}), 400

        # Parse due date (optional)
        due_date = None
        if payload.get("due_date"):
            try:
                due_date = datetime.fromisoformat(payload["due_date"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return jsonify({"error": "Invalid due date format. Use ISO 8601 format."}), 400

        # Create todo
        todo = Todo(
            user_id=user.id,
            text=text,
            completed=False,
            priority=priority,
            category=category or None,
            due_date=due_date,
        )
        db.session.add(todo)
        db.session.commit()

        app.logger.info(f"User {user.username} created todo: {todo.id}")
        return jsonify(serialize_todo(todo)), 201

    @app.patch("/api/todos/<int:todo_id>")
    @login_required
    @limiter.limit("60 per minute")
    def api_update_todo(todo_id: int):
        """Update a todo."""
        user = get_current_user()
        todo = Todo.query.filter_by(id=todo_id, user_id=user.id).first()
        if not todo:
            abort(404)

        payload: Dict[str, Any] = request.get_json(force=True, silent=True) or {}

        # Update text
        if "text" in payload:
            text = sanitize_string(payload.get("text", ""))
            is_valid, error = validate_todo_text(text)
            if not is_valid:
                return jsonify({"error": error}), 400
            todo.text = text

        # Update completed status
        if "completed" in payload:
            todo.completed = bool(payload["completed"])

        # Update priority
        if "priority" in payload:
            priority = payload["priority"]
            is_valid, error = validate_priority(priority)
            if not is_valid:
                return jsonify({"error": error}), 400
            todo.priority = priority

        # Update category
        if "category" in payload:
            category = sanitize_string(payload.get("category", ""))
            is_valid, error = validate_category(category)
            if not is_valid:
                return jsonify({"error": error}), 400
            todo.category = category or None

        # Update due date
        if "due_date" in payload:
            if payload["due_date"] is None:
                todo.due_date = None
            else:
                try:
                    todo.due_date = datetime.fromisoformat(
                        payload["due_date"].replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    return jsonify({"error": "Invalid due date format. Use ISO 8601 format."}), 400

        db.session.commit()
        app.logger.info(f"User {user.username} updated todo: {todo.id}")
        return jsonify(serialize_todo(todo))

    @app.delete("/api/todos/<int:todo_id>")
    @login_required
    @limiter.limit("60 per minute")
    def api_delete_todo(todo_id: int):
        """Delete a todo."""
        user = get_current_user()
        todo = Todo.query.filter_by(id=todo_id, user_id=user.id).first()
        if not todo:
            abort(404)

        db.session.delete(todo)
        db.session.commit()
        app.logger.info(f"User {user.username} deleted todo: {todo_id}")
        return ("", 204)

    # ---- User Profile API ----

    @app.get("/api/user/profile")
    @login_required
    def api_get_profile():
        """Get current user profile."""
        user = get_current_user()
        return jsonify({
            "id": user.id,
            "username": user.username,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        })

    @app.post("/api/user/change-password")
    @login_required
    @limiter.limit("5 per hour")
    def api_change_password():
        """Change user password."""
        user = get_current_user()
        payload: Dict[str, Any] = request.get_json(force=True, silent=True) or {}

        current_password = payload.get("current_password", "")
        new_password = payload.get("new_password", "")
        confirm_password = payload.get("confirm_password", "")

        # Verify current password
        if not user.check_password(current_password):
            app.logger.warning(f"Failed password change attempt for user: {user.username}")
            return jsonify({"error": "Current password is incorrect"}), 401

        # Validate new password
        is_valid, error = validate_password(new_password)
        if not is_valid:
            return jsonify({"error": error}), 400

        # Check confirmation
        if new_password != confirm_password:
            return jsonify({"error": "Passwords do not match"}), 400

        # Update password
        user.set_password(new_password)
        db.session.commit()

        app.logger.info(f"User {user.username} changed password")
        return jsonify({"message": "Password changed successfully"})

    @app.delete("/api/user/account")
    @login_required
    @limiter.limit("3 per day")
    def api_delete_account():
        """Delete user account and all associated data."""
        user = get_current_user()
        payload: Dict[str, Any] = request.get_json(force=True, silent=True) or {}

        password = payload.get("password", "")

        # Verify password before deletion
        if not user.check_password(password):
            app.logger.warning(f"Failed account deletion attempt for user: {user.username}")
            return jsonify({"error": "Password is incorrect"}), 401

        username = user.username
        db.session.delete(user)
        db.session.commit()
        session.clear()

        app.logger.info(f"User account deleted: {username}")
        return jsonify({"message": "Account deleted successfully"})

    # ---- Stats API ----

    @app.get("/api/stats")
    @login_required
    def api_get_stats():
        """Get user statistics."""
        user = get_current_user()

        total = Todo.query.filter_by(user_id=user.id).count()
        completed = Todo.query.filter_by(user_id=user.id, completed=True).count()
        active = total - completed

        # Count overdue tasks
        overdue = Todo.query.filter(
            Todo.user_id == user.id,
            Todo.completed == False,
            Todo.due_date != None,
            Todo.due_date < datetime.utcnow()
        ).count()

        # Count by priority
        high_priority = Todo.query.filter_by(
            user_id=user.id, completed=False, priority="high"
        ).count()

        return jsonify({
            "total": total,
            "completed": completed,
            "active": active,
            "overdue": overdue,
            "high_priority": high_priority,
        })


def serialize_todo(todo: Todo) -> dict[str, Any]:
    """Serialize Todo object to dictionary.

    Args:
        todo: Todo object to serialize

    Returns:
        Dictionary representation of todo
    """
    return {
        "id": todo.id,
        "text": todo.text,
        "completed": todo.completed,
        "priority": todo.priority,
        "category": todo.category,
        "due_date": todo.due_date.isoformat() if todo.due_date else None,
        "is_overdue": todo.is_overdue(),
        "created_at": todo.created_at.isoformat(),
        "updated_at": todo.updated_at.isoformat() if todo.updated_at else None,
    }


def register_error_handlers(app: Flask) -> None:
    """Register error handlers for common HTTP errors.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors."""
        return jsonify({"error": "Unauthorized"}), 401

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        if request.path.startswith("/api/"):
            return jsonify({"error": "Resource not found"}), 404
        return render_template("404.html"), 404

    @app.errorhandler(429)
    def ratelimit_handler(error):
        """Handle 429 Rate Limit Exceeded errors."""
        app.logger.warning(f"Rate limit exceeded from {request.remote_addr}")
        return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        db.session.rollback()
        app.logger.error(f"Internal error: {error}", exc_info=True)
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error"}), 500
        return render_template("500.html"), 500


# Create app instance
app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_ENV") != "production")
