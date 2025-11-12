from __future__ import annotations

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship

from database import db


class User(db.Model):
    """User model for authentication and authorization."""

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    todos = relationship("Todo", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        """Hash and set user password.

        Args:
            password: Plain text password
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash.

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User {self.username}>"


class Todo(db.Model):
    """Todo model for task management."""

    __tablename__ = "todo"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    text = db.Column(db.String(500), nullable=False)
    completed = db.Column(db.Boolean, default=False, nullable=False, index=True)
    priority = db.Column(db.String(20), default="medium", nullable=False)
    category = db.Column(db.String(50), nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="todos")

    def __repr__(self) -> str:
        """String representation of Todo."""
        return f"<Todo {self.id}: {self.text[:30]}>"

    def is_overdue(self) -> bool:
        """Check if task is overdue.

        Returns:
            True if task has a due date and it's in the past, False otherwise
        """
        if not self.due_date or self.completed:
            return False
        return self.due_date < datetime.utcnow()

