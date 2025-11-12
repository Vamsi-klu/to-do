"""Tests for database models."""
from __future__ import annotations

from datetime import datetime, timedelta
import pytest
from models import User, Todo


class TestUser:
    """Tests for User model."""

    def test_create_user(self, db):
        """Test creating a user."""
        user = User(username="newuser")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.username == "newuser"
        assert user.password_hash is not None
        assert user.password_hash != "password123"
        assert user.created_at is not None

    def test_password_hashing(self, db):
        """Test password hashing and verification."""
        user = User(username="testuser")
        user.set_password("SecretPassword123")
        db.session.add(user)
        db.session.commit()

        # Password should be hashed
        assert user.password_hash != "SecretPassword123"

        # Correct password should verify
        assert user.check_password("SecretPassword123") is True

        # Wrong password should not verify
        assert user.check_password("WrongPassword") is False
        assert user.check_password("secretpassword123") is False

    def test_unique_username(self, db, user):
        """Test username uniqueness constraint."""
        duplicate_user = User(username="testuser")
        duplicate_user.set_password("password123")
        db.session.add(duplicate_user)

        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            db.session.commit()

    def test_user_repr(self, user):
        """Test user string representation."""
        assert repr(user) == "<User testuser>"

    def test_user_todos_relationship(self, db, user):
        """Test user-todos relationship."""
        # Create todos for user
        todo1 = Todo(user_id=user.id, text="Todo 1", completed=False)
        todo2 = Todo(user_id=user.id, text="Todo 2", completed=True)
        db.session.add_all([todo1, todo2])
        db.session.commit()

        # User should have 2 todos
        assert len(user.todos) == 2
        assert todo1 in user.todos
        assert todo2 in user.todos

    def test_cascade_delete(self, db, user, todo):
        """Test that deleting user deletes their todos."""
        todo_id = todo.id
        user_id = user.id

        # Delete user
        db.session.delete(user)
        db.session.commit()

        # User should be deleted
        assert db.session.get(User, user_id) is None

        # Todo should also be deleted (cascade)
        assert db.session.get(Todo, todo_id) is None


class TestTodo:
    """Tests for Todo model."""

    def test_create_todo(self, db, user):
        """Test creating a todo."""
        todo = Todo(
            user_id=user.id,
            text="Buy groceries",
            completed=False,
            priority="high",
            category="shopping",
        )
        db.session.add(todo)
        db.session.commit()

        assert todo.id is not None
        assert todo.user_id == user.id
        assert todo.text == "Buy groceries"
        assert todo.completed is False
        assert todo.priority == "high"
        assert todo.category == "shopping"
        assert todo.created_at is not None
        assert todo.due_date is None

    def test_todo_defaults(self, db, user):
        """Test default values for todo fields."""
        todo = Todo(user_id=user.id, text="Test")
        db.session.add(todo)
        db.session.commit()

        assert todo.completed is False
        assert todo.priority == "medium"
        assert todo.category is None
        assert todo.due_date is None

    def test_todo_repr(self, todo):
        """Test todo string representation."""
        assert repr(todo) == "<Todo 1: Test todo>"

    def test_todo_user_relationship(self, db, user, todo):
        """Test todo-user relationship."""
        assert todo.user == user
        assert todo.user.username == "testuser"

    def test_is_overdue_no_due_date(self, todo):
        """Test is_overdue returns False when no due date."""
        assert todo.is_overdue() is False

    def test_is_overdue_future_date(self, db, user):
        """Test is_overdue returns False for future due date."""
        future_date = datetime.utcnow() + timedelta(days=1)
        todo = Todo(
            user_id=user.id,
            text="Future task",
            completed=False,
            due_date=future_date,
        )
        db.session.add(todo)
        db.session.commit()

        assert todo.is_overdue() is False

    def test_is_overdue_past_date(self, db, user):
        """Test is_overdue returns True for past due date."""
        past_date = datetime.utcnow() - timedelta(days=1)
        todo = Todo(
            user_id=user.id,
            text="Overdue task",
            completed=False,
            due_date=past_date,
        )
        db.session.add(todo)
        db.session.commit()

        assert todo.is_overdue() is True

    def test_is_overdue_completed_task(self, db, user):
        """Test is_overdue returns False for completed tasks."""
        past_date = datetime.utcnow() - timedelta(days=1)
        todo = Todo(
            user_id=user.id,
            text="Completed overdue task",
            completed=True,
            due_date=past_date,
        )
        db.session.add(todo)
        db.session.commit()

        # Completed tasks are never overdue
        assert todo.is_overdue() is False

    def test_todo_with_category(self, db, user):
        """Test creating todo with category."""
        todo = Todo(
            user_id=user.id,
            text="Work task",
            category="work",
        )
        db.session.add(todo)
        db.session.commit()

        assert todo.category == "work"

    def test_todo_without_category(self, db, user):
        """Test creating todo without category."""
        todo = Todo(
            user_id=user.id,
            text="General task",
        )
        db.session.add(todo)
        db.session.commit()

        assert todo.category is None

    def test_todo_priority_levels(self, db, user):
        """Test different priority levels."""
        low_todo = Todo(user_id=user.id, text="Low priority", priority="low")
        medium_todo = Todo(user_id=user.id, text="Medium priority", priority="medium")
        high_todo = Todo(user_id=user.id, text="High priority", priority="high")

        db.session.add_all([low_todo, medium_todo, high_todo])
        db.session.commit()

        assert low_todo.priority == "low"
        assert medium_todo.priority == "medium"
        assert high_todo.priority == "high"

    def test_updated_at_timestamp(self, db, user, todo):
        """Test that updated_at changes when todo is modified."""
        original_updated_at = todo.updated_at

        # Update todo
        todo.text = "Updated text"
        db.session.commit()

        # updated_at should change
        assert todo.updated_at != original_updated_at
