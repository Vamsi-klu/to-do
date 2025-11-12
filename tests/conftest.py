"""Pytest configuration and fixtures for testing."""

import pytest
import tempfile
import os
from datetime import datetime, timedelta

from app import create_app
from database import db as _db
from models import User, Todo


@pytest.fixture(scope='session')
def app():
    """Create and configure a test Flask application instance."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()

    test_app = create_app()
    test_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
    })

    # Create tables
    with test_app.app_context():
        _db.create_all()

    yield test_app

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='function')
def db(app):
    """Create a new database session for each test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app, db):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def user(db):
    """Create a test user."""
    user = User(username='testuser')
    user.set_password('testpassword')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def another_user(db):
    """Create another test user."""
    user = User(username='anotheruser')
    user.set_password('anotherpassword')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def todo(db, user):
    """Create a test todo item."""
    todo = Todo(
        user_id=user.id,
        text='Test todo item',
        notes='Some test notes',
        progress=50,
        completed=False
    )
    db.session.add(todo)
    db.session.commit()
    return todo


@pytest.fixture
def completed_todo(db, user):
    """Create a completed test todo item."""
    todo = Todo(
        user_id=user.id,
        text='Completed todo',
        notes='This is done',
        progress=100,
        completed=True
    )
    db.session.add(todo)
    db.session.commit()
    return todo


@pytest.fixture
def old_todo(db, user):
    """Create an old test todo item."""
    todo = Todo(
        user_id=user.id,
        text='Old todo',
        notes='Created a while ago',
        progress=25,
        completed=False
    )
    db.session.add(todo)
    db.session.flush()

    # Manually set old timestamps
    old_date = datetime.utcnow() - timedelta(days=10)
    todo.created_at = old_date
    todo.updated_at = old_date
    db.session.commit()
    return todo


@pytest.fixture
def multiple_todos(db, user):
    """Create multiple test todos."""
    todos = []
    for i in range(5):
        todo = Todo(
            user_id=user.id,
            text=f'Todo {i+1}',
            notes=f'Notes for todo {i+1}',
            progress=i * 20,
            completed=(i % 2 == 0)
        )
        db.session.add(todo)
        todos.append(todo)
    db.session.commit()
    return todos


@pytest.fixture
def authenticated_client(client, user):
    """Create an authenticated test client."""
    with client.session_transaction() as session:
        session['user_id'] = user.id
    return client


@pytest.fixture
def urgent_todo(db, user):
    """Create a todo with urgent keywords."""
    todo = Todo(
        user_id=user.id,
        text='Urgent: Complete critical task ASAP',
        notes='This is very important',
        progress=0,
        completed=False
    )
    db.session.add(todo)
    db.session.commit()
    return todo


@pytest.fixture
def meeting_todo(db, user):
    """Create a todo about a meeting."""
    todo = Todo(
        user_id=user.id,
        text='Schedule team meeting on Zoom',
        notes='Need to send calendar invites',
        progress=30,
        completed=False
    )
    db.session.add(todo)
    db.session.commit()
    return todo
