"""Pytest configuration and fixtures for testing."""
from __future__ import annotations

import os
import tempfile
from typing import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from database import db
from models import User, Todo


@pytest.fixture(scope="function")
def app() -> Generator[Flask, None, None]:
    """Create and configure a test Flask application instance.

    Uses an in-memory SQLite database for testing isolation.
    Each test gets a fresh application instance.
    """
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()

    # Configure app for testing
    test_config = {
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": False,
    }

    # Create app with test config
    test_app = create_app()
    test_app.config.update(test_config)

    # Create tables
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()

    # Clean up
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="function")
def client(app: Flask) -> FlaskClient:
    """Create a test client for making requests to the app.

    Args:
        app: The Flask application fixture

    Returns:
        FlaskClient: A test client for making HTTP requests
    """
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app: Flask):
    """Create a test CLI runner for testing CLI commands.

    Args:
        app: The Flask application fixture

    Returns:
        A test CLI runner
    """
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def test_user(app: Flask) -> User:
    """Create a test user in the database.

    Args:
        app: The Flask application fixture

    Returns:
        User: A test user with username 'testuser' and password 'testpass123'
    """
    with app.app_context():
        user = User(username="testuser")
        user.set_password("testpass123")
        db.session.add(user)
        db.session.commit()
        # Refresh to get the ID
        db.session.refresh(user)
        user_id = user.id
        username = user.username

    # Return a detached user object with the necessary attributes
    detached_user = User(username=username)
    detached_user.id = user_id
    return detached_user


@pytest.fixture(scope="function")
def another_user(app: Flask) -> User:
    """Create another test user for multi-user scenarios.

    Args:
        app: The Flask application fixture

    Returns:
        User: Another test user with username 'anotheruser' and password 'anotherpass123'
    """
    with app.app_context():
        user = User(username="anotheruser")
        user.set_password("anotherpass123")
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        user_id = user.id
        username = user.username

    detached_user = User(username=username)
    detached_user.id = user_id
    return detached_user


@pytest.fixture(scope="function")
def authenticated_client(client: FlaskClient, test_user: User) -> FlaskClient:
    """Create an authenticated test client.

    Args:
        client: The Flask test client
        test_user: A test user fixture

    Returns:
        FlaskClient: An authenticated test client with the test user logged in
    """
    # Log in the test user
    client.post("/login", data={
        "username": test_user.username,
        "password": "testpass123"
    }, follow_redirects=True)

    return client


@pytest.fixture(scope="function")
def test_todos(app: Flask, test_user: User) -> list[dict]:
    """Create sample todos for testing.

    Args:
        app: The Flask application fixture
        test_user: The test user fixture

    Returns:
        list[dict]: A list of todo dictionaries with id, text, and completed status
    """
    with app.app_context():
        todos_data = [
            {"text": "Buy groceries", "completed": False},
            {"text": "Write tests", "completed": True},
            {"text": "Deploy application", "completed": False},
        ]

        created_todos = []
        for todo_data in todos_data:
            todo = Todo(
                user_id=test_user.id,
                text=todo_data["text"],
                completed=todo_data["completed"]
            )
            db.session.add(todo)
            db.session.commit()
            db.session.refresh(todo)
            created_todos.append({
                "id": todo.id,
                "text": todo.text,
                "completed": todo.completed,
                "user_id": todo.user_id
            })

        return created_todos


@pytest.fixture(scope="function")
def app_context(app: Flask):
    """Provide an application context for tests that need it.

    Args:
        app: The Flask application fixture

    Yields:
        The application context
    """
    with app.app_context():
        yield
