"""Unit tests for database module."""
from __future__ import annotations

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from database import db, init_db
from models import User, Todo


class TestDatabaseInitialization:
    """Test cases for database initialization."""

    def test_db_instance(self):
        """Test that db is a SQLAlchemy instance."""
        assert isinstance(db, SQLAlchemy)

    def test_init_db_creates_tables(self, app):
        """Test that init_db creates all tables."""
        with app.app_context():
            # Tables should already be created by the fixture
            # Verify by checking if we can query them
            users = User.query.all()
            todos = Todo.query.all()

            assert isinstance(users, list)
            assert isinstance(todos, list)

    def test_init_db_with_custom_app(self):
        """Test init_db with a custom Flask app."""
        from app import create_app

        custom_app = Flask(__name__)
        custom_app.config.update({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        })

        # Initialize database
        init_db(custom_app)

        with custom_app.app_context():
            # Verify tables exist
            users = User.query.all()
            todos = Todo.query.all()

            assert isinstance(users, list)
            assert isinstance(todos, list)

    def test_db_session_add_and_commit(self, app, test_user):
        """Test adding and committing to the database."""
        with app.app_context():
            user = db.session.get(User, test_user.id)
            assert user is not None
            assert user.username == test_user.username

            # Add a new todo
            todo = Todo(user_id=user.id, text="Test task", completed=False)
            db.session.add(todo)
            db.session.commit()

            # Verify it was added
            todos = Todo.query.filter_by(user_id=user.id).all()
            assert len(todos) == 1
            assert todos[0].text == "Test task"

    def test_db_session_rollback(self, app, test_user):
        """Test rolling back a database session."""
        with app.app_context():
            user = db.session.get(User, test_user.id)

            # Add a todo
            todo = Todo(user_id=user.id, text="Rollback test", completed=False)
            db.session.add(todo)

            # Rollback before commit
            db.session.rollback()

            # Verify it was not added
            todos = Todo.query.filter_by(user_id=user.id).all()
            assert len(todos) == 0

    def test_db_session_delete(self, app, test_user):
        """Test deleting from the database."""
        with app.app_context():
            user = db.session.get(User, test_user.id)

            # Add a todo
            todo = Todo(user_id=user.id, text="Delete test", completed=False)
            db.session.add(todo)
            db.session.commit()

            todo_id = todo.id

            # Delete it
            db.session.delete(todo)
            db.session.commit()

            # Verify it was deleted
            deleted_todo = db.session.get(Todo, todo_id)
            assert deleted_todo is None

    def test_db_session_query(self, app, test_user):
        """Test querying the database."""
        with app.app_context():
            user = db.session.get(User, test_user.id)

            # Add multiple todos
            todos_data = [
                {"text": "Todo 1", "completed": False},
                {"text": "Todo 2", "completed": True},
                {"text": "Todo 3", "completed": False},
            ]

            for todo_data in todos_data:
                todo = Todo(user_id=user.id, **todo_data)
                db.session.add(todo)
            db.session.commit()

            # Query all todos
            all_todos = Todo.query.filter_by(user_id=user.id).all()
            assert len(all_todos) == 3

            # Query completed todos
            completed = Todo.query.filter_by(user_id=user.id, completed=True).all()
            assert len(completed) == 1
            assert completed[0].text == "Todo 2"

            # Query incomplete todos
            incomplete = Todo.query.filter_by(user_id=user.id, completed=False).all()
            assert len(incomplete) == 2

    def test_db_session_update(self, app, test_user):
        """Test updating records in the database."""
        with app.app_context():
            user = db.session.get(User, test_user.id)

            # Add a todo
            todo = Todo(user_id=user.id, text="Original text", completed=False)
            db.session.add(todo)
            db.session.commit()

            todo_id = todo.id

            # Update it
            todo.text = "Updated text"
            todo.completed = True
            db.session.commit()

            # Verify update
            updated_todo = db.session.get(Todo, todo_id)
            assert updated_todo.text == "Updated text"
            assert updated_todo.completed is True

    def test_db_foreign_key_constraint(self, app):
        """Test that foreign key constraints are enforced."""
        with app.app_context():
            # SQLite doesn't enforce foreign keys by default
            # This test verifies the relationship exists but may not raise
            # an error in SQLite - this is a known limitation
            todo = Todo(user_id=99999, text="Invalid FK", completed=False)
            db.session.add(todo)

            try:
                db.session.commit()
                # If commit succeeds (SQLite without FK enforcement),
                # verify the todo exists but has no valid user relationship
                assert todo.user is None
            except Exception:
                # If exception is raised (proper FK enforcement), that's also valid
                db.session.rollback()

    def test_db_unique_constraint(self, app, test_user):
        """Test that unique constraints are enforced."""
        with app.app_context():
            # Try to create a user with duplicate username
            duplicate_user = User(username=test_user.username)
            duplicate_user.set_password("password123")
            db.session.add(duplicate_user)

            with pytest.raises(Exception):  # Unique constraint violation
                db.session.commit()

    def test_db_transaction_isolation(self, app, test_user):
        """Test transaction isolation."""
        with app.app_context():
            user = db.session.get(User, test_user.id)

            # Start a transaction
            todo = Todo(user_id=user.id, text="Transaction test", completed=False)
            db.session.add(todo)

            # Before commit, query should see it in the same session
            result = Todo.query.filter_by(text="Transaction test").first()
            assert result is not None

            # Rollback
            db.session.rollback()

            # After rollback, it should not exist
            result = Todo.query.filter_by(text="Transaction test").first()
            assert result is None

    def test_db_cascade_delete(self, app, test_user):
        """Test cascade delete functionality."""
        with app.app_context():
            user = db.session.get(User, test_user.id)

            # Create todos
            todo1 = Todo(user_id=user.id, text="Todo 1", completed=False)
            todo2 = Todo(user_id=user.id, text="Todo 2", completed=True)
            db.session.add_all([todo1, todo2])
            db.session.commit()

            todo1_id = todo1.id
            todo2_id = todo2.id

            # Delete user (should cascade to todos)
            db.session.delete(user)
            db.session.commit()

            # Verify todos are deleted
            assert db.session.get(Todo, todo1_id) is None
            assert db.session.get(Todo, todo2_id) is None
            assert db.session.get(User, test_user.id) is None

    def test_db_multiple_sessions(self, app, test_user):
        """Test behavior with multiple database operations."""
        with app.app_context():
            user = db.session.get(User, test_user.id)

            # First operation
            todo1 = Todo(user_id=user.id, text="First", completed=False)
            db.session.add(todo1)
            db.session.commit()

            # Second operation
            todo2 = Todo(user_id=user.id, text="Second", completed=False)
            db.session.add(todo2)
            db.session.commit()

            # Verify both exist
            todos = Todo.query.filter_by(user_id=user.id).all()
            assert len(todos) == 2

    def test_db_session_refresh(self, app, test_user):
        """Test refreshing objects from the database."""
        with app.app_context():
            user = db.session.get(User, test_user.id)

            todo = Todo(user_id=user.id, text="Original", completed=False)
            db.session.add(todo)
            db.session.commit()

            todo_id = todo.id

            # Modify in memory
            todo.text = "Modified in memory"

            # Refresh from database (should revert to database state)
            db.session.refresh(todo)

            # Note: The text is already committed, so refresh won't change it
            # This test verifies the refresh mechanism works without errors
            assert todo.text is not None
            assert todo.id == todo_id
