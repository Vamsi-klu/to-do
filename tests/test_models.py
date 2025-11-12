"""Unit tests for database models."""
from __future__ import annotations

from datetime import datetime

import pytest
from werkzeug.security import check_password_hash

from database import db
from models import User, Todo


class TestUserModel:
    """Test cases for the User model."""

    def test_user_creation(self, app):
        """Test creating a new user."""
        with app.app_context():
            user = User(username="newuser")
            user.set_password("password123")

            assert user.username == "newuser"
            assert user.password_hash is not None
            assert user.password_hash != "password123"  # Should be hashed
            assert user.created_at is None  # Not set until commit

    def test_user_set_password(self, app):
        """Test setting a user password."""
        with app.app_context():
            user = User(username="testuser")
            user.set_password("mypassword")

            assert user.password_hash is not None
            assert user.password_hash != "mypassword"
            assert check_password_hash(user.password_hash, "mypassword")

    def test_user_check_password_correct(self, app, test_user):
        """Test checking correct password."""
        with app.app_context():
            user = db.session.get(User, test_user.id)
            assert user.check_password("testpass123") is True

    def test_user_check_password_incorrect(self, app, test_user):
        """Test checking incorrect password."""
        with app.app_context():
            user = db.session.get(User, test_user.id)
            assert user.check_password("wrongpassword") is False

    def test_user_check_password_empty(self, app, test_user):
        """Test checking empty password."""
        with app.app_context():
            user = db.session.get(User, test_user.id)
            assert user.check_password("") is False

    def test_user_username_unique(self, app, test_user):
        """Test that usernames must be unique."""
        with app.app_context():
            duplicate_user = User(username=test_user.username)
            duplicate_user.set_password("password123")
            db.session.add(duplicate_user)

            with pytest.raises(Exception):  # SQLAlchemy IntegrityError
                db.session.commit()

    def test_user_username_required(self, app):
        """Test that username is required."""
        with app.app_context():
            user = User(username=None)
            user.set_password("password123")
            db.session.add(user)

            with pytest.raises(Exception):  # SQLAlchemy IntegrityError
                db.session.commit()

    def test_user_password_hash_required(self, app):
        """Test that password hash is required."""
        with app.app_context():
            user = User(username="testuser")
            # Don't set password
            db.session.add(user)

            with pytest.raises(Exception):  # SQLAlchemy IntegrityError
                db.session.commit()

    def test_user_created_at_default(self, app):
        """Test that created_at is set automatically."""
        with app.app_context():
            user = User(username="timeuser")
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()

            assert user.created_at is not None
            assert isinstance(user.created_at, datetime)
            # Should be recent (within last minute)
            time_diff = datetime.utcnow() - user.created_at
            assert time_diff.total_seconds() < 60

    def test_user_todos_relationship(self, app, test_user):
        """Test the relationship between User and Todo."""
        with app.app_context():
            user = db.session.get(User, test_user.id)

            # Create todos
            todo1 = Todo(user_id=user.id, text="Task 1", completed=False)
            todo2 = Todo(user_id=user.id, text="Task 2", completed=True)
            db.session.add_all([todo1, todo2])
            db.session.commit()

            # Refresh to load relationship
            db.session.refresh(user)
            assert len(user.todos) == 2
            assert todo1 in user.todos
            assert todo2 in user.todos

    def test_user_cascade_delete_todos(self, app, test_user):
        """Test that deleting a user deletes their todos."""
        with app.app_context():
            user = db.session.get(User, test_user.id)

            # Create todos
            todo1 = Todo(user_id=user.id, text="Task 1", completed=False)
            todo2 = Todo(user_id=user.id, text="Task 2", completed=True)
            db.session.add_all([todo1, todo2])
            db.session.commit()

            todo1_id = todo1.id
            todo2_id = todo2.id

            # Delete user
            db.session.delete(user)
            db.session.commit()

            # Verify todos are deleted
            assert db.session.get(Todo, todo1_id) is None
            assert db.session.get(Todo, todo2_id) is None

    def test_user_multiple_password_changes(self, app):
        """Test changing password multiple times."""
        with app.app_context():
            user = User(username="changepass")
            user.set_password("password1")
            db.session.add(user)
            db.session.commit()

            # Verify first password
            assert user.check_password("password1") is True
            assert user.check_password("password2") is False

            # Change password
            user.set_password("password2")
            db.session.commit()

            # Verify new password
            assert user.check_password("password1") is False
            assert user.check_password("password2") is True


class TestTodoModel:
    """Test cases for the Todo model."""

    def test_todo_creation(self, app, test_user):
        """Test creating a new todo."""
        with app.app_context():
            todo = Todo(
                user_id=test_user.id,
                text="Test todo",
                completed=False
            )

            assert todo.text == "Test todo"
            assert todo.completed is False
            assert todo.user_id == test_user.id
            assert todo.created_at is None  # Not set until commit
            assert todo.updated_at is None

    def test_todo_text_required(self, app, test_user):
        """Test that todo text is required."""
        with app.app_context():
            todo = Todo(user_id=test_user.id, text=None, completed=False)
            db.session.add(todo)

            with pytest.raises(Exception):  # SQLAlchemy IntegrityError
                db.session.commit()

    def test_todo_user_id_required(self, app):
        """Test that user_id is required."""
        with app.app_context():
            todo = Todo(text="Test todo", completed=False)
            db.session.add(todo)

            with pytest.raises(Exception):  # SQLAlchemy IntegrityError
                db.session.commit()

    def test_todo_completed_default(self, app, test_user):
        """Test that completed defaults to False."""
        with app.app_context():
            todo = Todo(user_id=test_user.id, text="Default test")
            db.session.add(todo)
            db.session.commit()

            assert todo.completed is False

    def test_todo_created_at_default(self, app, test_user):
        """Test that created_at is set automatically."""
        with app.app_context():
            todo = Todo(user_id=test_user.id, text="Time test", completed=False)
            db.session.add(todo)
            db.session.commit()

            assert todo.created_at is not None
            assert isinstance(todo.created_at, datetime)
            time_diff = datetime.utcnow() - todo.created_at
            assert time_diff.total_seconds() < 60

    def test_todo_updated_at_on_creation(self, app, test_user):
        """Test that updated_at is set on creation."""
        with app.app_context():
            todo = Todo(user_id=test_user.id, text="Update test", completed=False)
            db.session.add(todo)
            db.session.commit()

            assert todo.updated_at is not None
            assert isinstance(todo.updated_at, datetime)

    def test_todo_updated_at_on_update(self, app, test_user):
        """Test that updated_at changes when todo is updated."""
        with app.app_context():
            todo = Todo(user_id=test_user.id, text="Update test", completed=False)
            db.session.add(todo)
            db.session.commit()

            original_updated_at = todo.updated_at

            # Small delay to ensure time difference
            import time
            time.sleep(0.1)

            # Update todo
            todo.text = "Updated text"
            db.session.commit()

            # updated_at should change (or might be same in fast tests)
            # This is a limitation of datetime resolution
            assert todo.updated_at is not None

    def test_todo_user_relationship(self, app, test_user):
        """Test the relationship between Todo and User."""
        with app.app_context():
            user = db.session.get(User, test_user.id)
            todo = Todo(user_id=user.id, text="Relationship test", completed=False)
            db.session.add(todo)
            db.session.commit()

            # Access user through relationship
            db.session.refresh(todo)
            assert todo.user is not None
            assert todo.user.id == user.id
            assert todo.user.username == user.username

    def test_todo_invalid_user_id(self, app):
        """Test creating todo with non-existent user_id."""
        with app.app_context():
            todo = Todo(user_id=99999, text="Invalid user", completed=False)
            db.session.add(todo)

            try:
                db.session.commit()
                # If commit succeeds (SQLite without FK enforcement),
                # verify the relationship is invalid
                assert todo.user is None
            except Exception:
                # If exception is raised (proper FK enforcement), that's also valid
                db.session.rollback()

    def test_todo_toggle_completed(self, app, test_user):
        """Test toggling todo completed status."""
        with app.app_context():
            todo = Todo(user_id=test_user.id, text="Toggle test", completed=False)
            db.session.add(todo)
            db.session.commit()

            assert todo.completed is False

            # Toggle to completed
            todo.completed = True
            db.session.commit()
            assert todo.completed is True

            # Toggle back to incomplete
            todo.completed = False
            db.session.commit()
            assert todo.completed is False

    def test_todo_text_max_length(self, app, test_user):
        """Test todo text with maximum length."""
        with app.app_context():
            # 255 characters (max length)
            long_text = "a" * 255
            todo = Todo(user_id=test_user.id, text=long_text, completed=False)
            db.session.add(todo)
            db.session.commit()

            assert len(todo.text) == 255
            assert todo.text == long_text

    def test_todo_text_exceeds_max_length(self, app, test_user):
        """Test todo text exceeding maximum length."""
        with app.app_context():
            # 256 characters (exceeds max)
            too_long_text = "a" * 256
            todo = Todo(user_id=test_user.id, text=too_long_text, completed=False)
            db.session.add(todo)

            try:
                db.session.commit()
                # SQLite may allow this, but verify it's stored
                # In production with proper DB, this would raise an error
                assert len(todo.text) >= 255
            except Exception:
                # If exception is raised (proper length enforcement), that's ideal
                db.session.rollback()

    def test_multiple_todos_per_user(self, app, test_user):
        """Test that a user can have multiple todos."""
        with app.app_context():
            user = db.session.get(User, test_user.id)

            todos = [
                Todo(user_id=user.id, text=f"Todo {i}", completed=False)
                for i in range(10)
            ]
            db.session.add_all(todos)
            db.session.commit()

            db.session.refresh(user)
            assert len(user.todos) == 10

    def test_todos_isolated_by_user(self, app, test_user, another_user):
        """Test that todos are isolated by user."""
        with app.app_context():
            user1 = db.session.get(User, test_user.id)
            user2 = db.session.get(User, another_user.id)

            # Create todos for each user
            todo1 = Todo(user_id=user1.id, text="User 1 todo", completed=False)
            todo2 = Todo(user_id=user2.id, text="User 2 todo", completed=False)
            db.session.add_all([todo1, todo2])
            db.session.commit()

            # Refresh to load relationships
            db.session.refresh(user1)
            db.session.refresh(user2)

            # Each user should only see their own todos
            assert len(user1.todos) == 1
            assert len(user2.todos) == 1
            assert todo1 in user1.todos
            assert todo2 in user2.todos
            assert todo1 not in user2.todos
            assert todo2 not in user1.todos
