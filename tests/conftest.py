"""Pytest configuration and fixtures."""
from __future__ import annotations

import pytest
from app import create_app
from database import db as _db
from models import User, Todo


@pytest.fixture(scope="function")
def app():
    """Create and configure a test application instance."""
    app = create_app("testing")
    yield app


@pytest.fixture(scope="function")
def db(app):
    """Create a test database and drop it after the test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app, db):
    """Create a test client."""
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def user(db):
    """Create a test user."""
    user = User(username="testuser")
    user.set_password("Test123456")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope="function")
def another_user(db):
    """Create another test user for authorization tests."""
    user = User(username="anotheruser")
    user.set_password("Another123456")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope="function")
def authenticated_client(client, user):
    """Create an authenticated test client."""
    with client.session_transaction() as sess:
        sess["user_id"] = user.id
    return client


@pytest.fixture(scope="function")
def todo(db, user):
    """Create a test todo."""
    todo = Todo(
        user_id=user.id,
        text="Test todo",
        completed=False,
        priority="medium",
    )
    db.session.add(todo)
    db.session.commit()
    return todo


@pytest.fixture(scope="function")
def completed_todo(db, user):
    """Create a completed test todo."""
    todo = Todo(
        user_id=user.id,
        text="Completed todo",
        completed=True,
        priority="low",
    )
    db.session.add(todo)
    db.session.commit()
    return todo
