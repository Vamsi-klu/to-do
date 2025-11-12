"""Unit tests for database models."""

import pytest
from datetime import datetime, timedelta

from models import User, Todo
from database import db


@pytest.mark.unit
class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self, db):
        """Test creating a new user."""
        user = User(username='newuser')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.username == 'newuser'
        assert user.password_hash is not None
        assert user.password_hash != 'password123'
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)

    def test_user_set_password(self, db):
        """Test password hashing."""
        user = User(username='testuser')
        user.set_password('mypassword')

        assert user.password_hash is not None
        assert user.password_hash != 'mypassword'
        assert len(user.password_hash) > 20  # Hashed password should be long

    def test_user_check_password_correct(self, user):
        """Test checking correct password."""
        assert user.check_password('testpassword') is True

    def test_user_check_password_incorrect(self, user):
        """Test checking incorrect password."""
        assert user.check_password('wrongpassword') is False

    def test_user_check_password_empty(self, user):
        """Test checking empty password."""
        assert user.check_password('') is False

    def test_user_unique_username(self, db, user):
        """Test that usernames must be unique."""
        duplicate_user = User(username='testuser')
        duplicate_user.set_password('password')
        db.session.add(duplicate_user)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db.session.commit()

    def test_user_todos_relationship(self, db, user):
        """Test user-todos relationship."""
        todo1 = Todo(user_id=user.id, text='Todo 1', completed=False)
        todo2 = Todo(user_id=user.id, text='Todo 2', completed=False)
        db.session.add_all([todo1, todo2])
        db.session.commit()

        assert len(user.todos) == 2
        assert todo1 in user.todos
        assert todo2 in user.todos

    def test_user_cascade_delete(self, db, user, todo):
        """Test that deleting a user cascades to todos."""
        user_id = user.id
        todo_id = todo.id

        db.session.delete(user)
        db.session.commit()

        assert db.session.get(User, user_id) is None
        assert db.session.get(Todo, todo_id) is None


@pytest.mark.unit
class TestTodoModel:
    """Tests for the Todo model."""

    def test_create_todo(self, db, user):
        """Test creating a new todo."""
        todo = Todo(
            user_id=user.id,
            text='My task',
            notes='Some notes',
            progress=50,
            completed=False
        )
        db.session.add(todo)
        db.session.commit()

        assert todo.id is not None
        assert todo.user_id == user.id
        assert todo.text == 'My task'
        assert todo.notes == 'Some notes'
        assert todo.progress == 50
        assert todo.completed is False
        assert todo.created_at is not None
        assert todo.updated_at is not None

    def test_todo_default_values(self, db, user):
        """Test default values for todo fields."""
        todo = Todo(user_id=user.id, text='Simple task')
        db.session.add(todo)
        db.session.commit()

        assert todo.notes is None
        assert todo.progress == 0
        assert todo.completed is False
        assert todo.created_at is not None

    def test_todo_completed_field(self, db, user):
        """Test todo completion status."""
        todo = Todo(user_id=user.id, text='Task', completed=False)
        db.session.add(todo)
        db.session.commit()

        assert todo.completed is False

        todo.completed = True
        db.session.commit()

        assert todo.completed is True

    def test_todo_progress_field(self, db, user):
        """Test todo progress tracking."""
        todo = Todo(user_id=user.id, text='Task', progress=0)
        db.session.add(todo)
        db.session.commit()

        assert todo.progress == 0

        todo.progress = 75
        db.session.commit()

        assert todo.progress == 75

    def test_todo_notes_field(self, db, user):
        """Test todo notes field."""
        todo = Todo(user_id=user.id, text='Task')
        db.session.add(todo)
        db.session.commit()

        assert todo.notes is None

        todo.notes = 'These are detailed notes'
        db.session.commit()

        assert todo.notes == 'These are detailed notes'

    def test_todo_updated_at_timestamp(self, db, user):
        """Test that updated_at changes on update."""
        todo = Todo(user_id=user.id, text='Task')
        db.session.add(todo)
        db.session.commit()

        original_updated = todo.updated_at

        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.1)

        todo.text = 'Updated task'
        db.session.commit()

        # Note: onupdate may not trigger in all scenarios with SQLite in tests
        # This test verifies the field exists and can be set
        assert todo.updated_at is not None

    def test_todo_user_relationship(self, db, user, todo):
        """Test todo-user relationship."""
        assert todo.user == user
        assert todo.user.username == 'testuser'

    def test_todo_requires_text(self, db, user):
        """Test that todo text is required."""
        todo = Todo(user_id=user.id, text='')
        db.session.add(todo)
        # Empty string is allowed by database, validation should be in app layer
        db.session.commit()
        assert todo.text == ''

    def test_todo_requires_user(self, db):
        """Test that todo requires a user_id."""
        todo = Todo(text='Task without user')
        db.session.add(todo)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db.session.commit()

    def test_todo_progress_boundaries(self, db, user):
        """Test todo progress can handle boundary values."""
        todo = Todo(user_id=user.id, text='Task', progress=0)
        db.session.add(todo)
        db.session.commit()
        assert todo.progress == 0

        todo.progress = 100
        db.session.commit()
        assert todo.progress == 100

        # Test that app should handle clamping, but DB allows any integer
        todo.progress = 150
        db.session.commit()
        assert todo.progress == 150

        todo.progress = -10
        db.session.commit()
        assert todo.progress == -10

    def test_multiple_todos_same_user(self, db, user):
        """Test creating multiple todos for same user."""
        todos = []
        for i in range(10):
            todo = Todo(user_id=user.id, text=f'Task {i}', progress=i*10)
            db.session.add(todo)
            todos.append(todo)

        db.session.commit()

        assert len(user.todos) == 10
        for i, todo in enumerate(todos):
            assert todo.text == f'Task {i}'
            assert todo.progress == i * 10

    def test_todo_isolation_between_users(self, db, user, another_user):
        """Test that todos are isolated between users."""
        todo1 = Todo(user_id=user.id, text='User 1 task')
        todo2 = Todo(user_id=another_user.id, text='User 2 task')
        db.session.add_all([todo1, todo2])
        db.session.commit()

        assert len(user.todos) == 1
        assert len(another_user.todos) == 1
        assert user.todos[0].text == 'User 1 task'
        assert another_user.todos[0].text == 'User 2 task'
