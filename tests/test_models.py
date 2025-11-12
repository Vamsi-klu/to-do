"""Unit tests for database models."""
import pytest
from datetime import datetime
from models import User, Todo


@pytest.mark.unit
class TestUserModel:
    """Test User model."""

    def test_create_user(self, db):
        """Test creating a user."""
        user = User(username='testuser')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.username == 'testuser'
        assert user.password_hash is not None
        assert user.password_hash != 'testpass'

    def test_password_hashing(self, db):
        """Test password hashing and verification."""
        user = User(username='testuser')
        user.set_password('mypassword')

        assert user.check_password('mypassword') is True
        assert user.check_password('wrongpassword') is False

    def test_user_unique_username(self, db):
        """Test that usernames must be unique."""
        user1 = User(username='duplicate')
        user1.set_password('pass1')
        db.session.add(user1)
        db.session.commit()

        user2 = User(username='duplicate')
        user2.set_password('pass2')
        db.session.add(user2)

        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()

    def test_user_todos_relationship(self, db, test_user, test_todos):
        """Test user-todos relationship."""
        user = db.session.get(User, test_user.id)
        assert len(user.todos) == 5
        assert all(todo.user_id == user.id for todo in user.todos)


@pytest.mark.unit
class TestTodoModel:
    """Test Todo model."""

    def test_create_todo(self, db, test_user):
        """Test creating a todo."""
        todo = Todo(
            user_id=test_user.id,
            text='Test task',
            completed=False
        )
        db.session.add(todo)
        db.session.commit()

        assert todo.id is not None
        assert todo.text == 'Test task'
        assert todo.completed is False
        assert todo.user_id == test_user.id
        assert isinstance(todo.created_at, datetime)

    def test_todo_default_values(self, db, test_user):
        """Test todo default values."""
        todo = Todo(user_id=test_user.id, text='Task')
        db.session.add(todo)
        db.session.commit()

        assert todo.completed is False
        assert todo.updated_at is not None
        assert todo.created_at is not None
        assert isinstance(todo.updated_at, datetime)
        assert isinstance(todo.created_at, datetime)

    def test_update_todo(self, db, test_user):
        """Test updating a todo."""
        todo = Todo(user_id=test_user.id, text='Original', completed=False)
        db.session.add(todo)
        db.session.commit()

        # Update
        todo.text = 'Updated'
        todo.completed = True
        db.session.commit()

        # Verify
        updated_todo = db.session.get(Todo, todo.id)
        assert updated_todo.text == 'Updated'
        assert updated_todo.completed is True

    def test_delete_todo(self, db, test_user):
        """Test deleting a todo."""
        todo = Todo(user_id=test_user.id, text='To delete', completed=False)
        db.session.add(todo)
        db.session.commit()
        todo_id = todo.id

        db.session.delete(todo)
        db.session.commit()

        deleted_todo = db.session.get(Todo, todo_id)
        assert deleted_todo is None

    def test_todo_user_relationship(self, db, test_user):
        """Test todo-user relationship."""
        todo = Todo(user_id=test_user.id, text='Task', completed=False)
        db.session.add(todo)
        db.session.commit()

        assert todo.user is not None
        assert todo.user.id == test_user.id
        assert todo.user.username == test_user.username
