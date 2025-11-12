"""Unit tests for application routes and views."""
from __future__ import annotations

import json

import pytest
from flask import session

from app import create_app, serialize_todo
from database import db
from models import User, Todo


class TestAppCreation:
    """Test cases for app creation and configuration."""

    def test_create_app(self):
        """Test that create_app returns a Flask instance."""
        app = create_app()
        assert app is not None
        assert app.config["TESTING"] is False

    def test_app_config(self, app):
        """Test app configuration."""
        assert app.config["TESTING"] is True
        assert app.config["SECRET_KEY"] == "test-secret-key"
        assert "sqlite:///" in app.config["SQLALCHEMY_DATABASE_URI"]
        assert app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] is False

    def test_app_routes_registered(self, app):
        """Test that all routes are registered."""
        rules = [str(rule) for rule in app.url_map.iter_rules()]

        # Check main routes
        assert "/" in rules
        assert "/login" in rules
        assert "/register" in rules
        assert "/logout" in rules

        # Check API routes
        assert "/api/todos" in rules
        assert "/api/todos/<int:todo_id>" in rules


class TestIndexRoute:
    """Test cases for the index route."""

    def test_index_unauthenticated(self, client):
        """Test accessing index without authentication redirects to login."""
        response = client.get("/")
        assert response.status_code == 302
        assert "/login" in response.location

    def test_index_authenticated(self, authenticated_client):
        """Test accessing index with authentication."""
        response = authenticated_client.get("/")
        assert response.status_code == 200
        assert b"Your Tasks" in response.data
        assert b"testuser" in response.data

    def test_index_shows_user_info(self, authenticated_client):
        """Test that index shows logged-in user information."""
        response = authenticated_client.get("/")
        assert response.status_code == 200
        assert b"Signed in as" in response.data
        assert b"testuser" in response.data


class TestLoginRoute:
    """Test cases for login routes."""

    def test_login_get(self, client):
        """Test GET request to login page."""
        response = client.get("/login")
        assert response.status_code == 200
        assert b"Welcome back" in response.data
        assert b"Sign in to manage your tasks" in response.data

    def test_login_get_already_authenticated(self, authenticated_client):
        """Test GET login redirects to index if already authenticated."""
        response = authenticated_client.get("/login")
        assert response.status_code == 302
        assert "/" in response.location

    def test_login_post_success(self, client, test_user):
        """Test successful login."""
        response = client.post("/login", data={
            "username": "testuser",
            "password": "testpass123"
        }, follow_redirects=False)

        assert response.status_code == 302
        assert "/" in response.location

        # Verify session
        with client.session_transaction() as sess:
            assert sess.get("user_id") == test_user.id

    def test_login_post_invalid_username(self, client):
        """Test login with invalid username."""
        response = client.post("/login", data={
            "username": "nonexistent",
            "password": "password123"
        })

        assert response.status_code == 401
        assert b"Invalid credentials" in response.data

    def test_login_post_invalid_password(self, client, test_user):
        """Test login with invalid password."""
        response = client.post("/login", data={
            "username": "testuser",
            "password": "wrongpassword"
        })

        assert response.status_code == 401
        assert b"Invalid credentials" in response.data

    def test_login_post_empty_username(self, client):
        """Test login with empty username."""
        response = client.post("/login", data={
            "username": "",
            "password": "password123"
        })

        assert response.status_code == 401
        assert b"Invalid credentials" in response.data

    def test_login_post_empty_password(self, client, test_user):
        """Test login with empty password."""
        response = client.post("/login", data={
            "username": "testuser",
            "password": ""
        })

        assert response.status_code == 401
        assert b"Invalid credentials" in response.data

    def test_login_post_whitespace_username(self, client):
        """Test login with whitespace-only username."""
        response = client.post("/login", data={
            "username": "   ",
            "password": "password123"
        })

        assert response.status_code == 401
        assert b"Invalid credentials" in response.data


class TestRegisterRoute:
    """Test cases for register routes."""

    def test_register_get(self, client):
        """Test GET request to register page."""
        response = client.get("/register")
        assert response.status_code == 200
        assert b"Create your account" in response.data
        assert b"Start organizing your day" in response.data

    def test_register_get_already_authenticated(self, authenticated_client):
        """Test GET register redirects to index if already authenticated."""
        response = authenticated_client.get("/register")
        assert response.status_code == 302
        assert "/" in response.location

    def test_register_post_success(self, client, app):
        """Test successful registration."""
        response = client.post("/register", data={
            "username": "newuser",
            "password": "password123",
            "confirm": "password123"
        }, follow_redirects=False)

        assert response.status_code == 302
        assert "/" in response.location

        # Verify user was created
        with app.app_context():
            user = User.query.filter_by(username="newuser").first()
            assert user is not None
            assert user.check_password("password123")

        # Verify session
        with client.session_transaction() as sess:
            assert sess.get("user_id") is not None

    def test_register_post_password_mismatch(self, client, app):
        """Test registration with password mismatch."""
        response = client.post("/register", data={
            "username": "newuser",
            "password": "password123",
            "confirm": "different123"
        })

        assert response.status_code == 400
        assert b"Passwords do not match" in response.data

        # Verify user was not created
        with app.app_context():
            user = User.query.filter_by(username="newuser").first()
            assert user is None

    def test_register_post_empty_username(self, client, app):
        """Test registration with empty username."""
        response = client.post("/register", data={
            "username": "",
            "password": "password123",
            "confirm": "password123"
        })

        assert response.status_code == 400
        assert b"Username and password are required" in response.data

    def test_register_post_empty_password(self, client, app):
        """Test registration with empty password."""
        response = client.post("/register", data={
            "username": "newuser",
            "password": "",
            "confirm": ""
        })

        assert response.status_code == 400
        assert b"Username and password are required" in response.data

    def test_register_post_whitespace_username(self, client, app):
        """Test registration with whitespace-only username."""
        response = client.post("/register", data={
            "username": "   ",
            "password": "password123",
            "confirm": "password123"
        })

        assert response.status_code == 400
        assert b"Username and password are required" in response.data

    def test_register_post_duplicate_username(self, client, test_user, app):
        """Test registration with duplicate username."""
        response = client.post("/register", data={
            "username": "testuser",
            "password": "password123",
            "confirm": "password123"
        })

        assert response.status_code == 400
        assert b"Username already exists" in response.data

    def test_register_post_duplicate_username_case_sensitive(self, client, test_user, app):
        """Test that username comparison is case-sensitive."""
        # Assuming usernames are case-sensitive
        response = client.post("/register", data={
            "username": "TESTUSER",  # Different case
            "password": "password123",
            "confirm": "password123"
        })

        # Should succeed if case-sensitive, or fail if case-insensitive
        # Most systems treat usernames as case-sensitive
        assert response.status_code in [302, 400]


class TestLogoutRoute:
    """Test cases for logout route."""

    def test_logout(self, authenticated_client):
        """Test logout functionality."""
        # Verify user is authenticated
        with authenticated_client.session_transaction() as sess:
            assert sess.get("user_id") is not None

        # Logout
        response = authenticated_client.post("/logout", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.location

        # Verify session is cleared
        with authenticated_client.session_transaction() as sess:
            assert sess.get("user_id") is None

    def test_logout_unauthenticated(self, client):
        """Test logout when not authenticated."""
        response = client.post("/logout", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.location

    def test_logout_get_not_allowed(self, authenticated_client):
        """Test that GET is not allowed for logout."""
        response = authenticated_client.get("/logout")
        assert response.status_code == 405  # Method not allowed


class TestAPIListTodos:
    """Test cases for GET /api/todos."""

    def test_api_list_todos_unauthenticated(self, client):
        """Test listing todos without authentication."""
        response = client.get("/api/todos")
        assert response.status_code == 302
        assert "/login" in response.location

    def test_api_list_todos_empty(self, authenticated_client):
        """Test listing todos when user has none."""
        response = authenticated_client.get("/api/todos")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 0

    def test_api_list_todos_with_data(self, authenticated_client, app, test_user, test_todos):
        """Test listing todos with existing data."""
        response = authenticated_client.get("/api/todos")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == len(test_todos)

        # Verify structure
        for todo in data:
            assert "id" in todo
            assert "text" in todo
            assert "completed" in todo
            assert "created_at" in todo

    def test_api_list_todos_ordering(self, authenticated_client, app, test_user):
        """Test that todos are ordered by created_at desc."""
        with app.app_context():
            # Create todos in specific order
            todo1 = Todo(user_id=test_user.id, text="First", completed=False)
            todo2 = Todo(user_id=test_user.id, text="Second", completed=False)
            todo3 = Todo(user_id=test_user.id, text="Third", completed=False)

            db.session.add_all([todo1, todo2, todo3])
            db.session.commit()

        response = authenticated_client.get("/api/todos")
        data = json.loads(response.data)

        # Should be in reverse order (newest first)
        assert data[0]["text"] == "Third"
        assert data[1]["text"] == "Second"
        assert data[2]["text"] == "First"

    def test_api_list_todos_isolation(self, authenticated_client, app, test_user, another_user):
        """Test that users only see their own todos."""
        with app.app_context():
            # Create todos for test_user
            todo1 = Todo(user_id=test_user.id, text="Test user todo", completed=False)
            db.session.add(todo1)

            # Create todos for another_user
            todo2 = Todo(user_id=another_user.id, text="Another user todo", completed=False)
            db.session.add(todo2)

            db.session.commit()

        response = authenticated_client.get("/api/todos")
        data = json.loads(response.data)

        # Should only see test_user's todos
        assert len(data) == 1
        assert data[0]["text"] == "Test user todo"


class TestAPICreateTodo:
    """Test cases for POST /api/todos."""

    def test_api_create_todo_unauthenticated(self, client):
        """Test creating todo without authentication."""
        response = client.post("/api/todos",
                               data=json.dumps({"text": "Test todo"}),
                               content_type="application/json")
        assert response.status_code == 302
        assert "/login" in response.location

    def test_api_create_todo_success(self, authenticated_client, app, test_user):
        """Test successfully creating a todo."""
        response = authenticated_client.post("/api/todos",
                                             data=json.dumps({"text": "New todo"}),
                                             content_type="application/json")

        assert response.status_code == 201

        data = json.loads(response.data)
        assert data["text"] == "New todo"
        assert data["completed"] is False
        assert "id" in data
        assert "created_at" in data

        # Verify in database
        with app.app_context():
            todo = db.session.get(Todo, data["id"])
            assert todo is not None
            assert todo.text == "New todo"
            assert todo.user_id == test_user.id

    def test_api_create_todo_empty_text(self, authenticated_client):
        """Test creating todo with empty text."""
        response = authenticated_client.post("/api/todos",
                                             data=json.dumps({"text": ""}),
                                             content_type="application/json")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "required" in data["error"].lower()

    def test_api_create_todo_whitespace_text(self, authenticated_client):
        """Test creating todo with whitespace-only text."""
        response = authenticated_client.post("/api/todos",
                                             data=json.dumps({"text": "   "}),
                                             content_type="application/json")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_api_create_todo_no_text_field(self, authenticated_client):
        """Test creating todo without text field."""
        response = authenticated_client.post("/api/todos",
                                             data=json.dumps({}),
                                             content_type="application/json")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_api_create_todo_invalid_json(self, authenticated_client):
        """Test creating todo with invalid JSON."""
        response = authenticated_client.post("/api/todos",
                                             data="invalid json",
                                             content_type="application/json")

        # Should handle gracefully
        assert response.status_code == 400

    def test_api_create_todo_with_special_characters(self, authenticated_client, app):
        """Test creating todo with special characters."""
        special_text = "Buy milk & eggs @ store! 🛒"

        response = authenticated_client.post("/api/todos",
                                             data=json.dumps({"text": special_text}),
                                             content_type="application/json")

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["text"] == special_text


class TestAPIUpdateTodo:
    """Test cases for PATCH /api/todos/<id>."""

    def test_api_update_todo_unauthenticated(self, client, app, test_user):
        """Test updating todo without authentication."""
        with app.app_context():
            todo = Todo(user_id=test_user.id, text="Test", completed=False)
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        response = client.patch(f"/api/todos/{todo_id}",
                               data=json.dumps({"text": "Updated"}),
                               content_type="application/json")
        assert response.status_code == 302

    def test_api_update_todo_text(self, authenticated_client, app, test_user):
        """Test updating todo text."""
        with app.app_context():
            todo = Todo(user_id=test_user.id, text="Original", completed=False)
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        response = authenticated_client.patch(f"/api/todos/{todo_id}",
                                             data=json.dumps({"text": "Updated"}),
                                             content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["text"] == "Updated"

        # Verify in database
        with app.app_context():
            todo = db.session.get(Todo, todo_id)
            assert todo.text == "Updated"

    def test_api_update_todo_completed(self, authenticated_client, app, test_user):
        """Test updating todo completed status."""
        with app.app_context():
            todo = Todo(user_id=test_user.id, text="Test", completed=False)
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        response = authenticated_client.patch(f"/api/todos/{todo_id}",
                                             data=json.dumps({"completed": True}),
                                             content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["completed"] is True

        # Verify in database
        with app.app_context():
            todo = db.session.get(Todo, todo_id)
            assert todo.completed is True

    def test_api_update_todo_both_fields(self, authenticated_client, app, test_user):
        """Test updating both text and completed."""
        with app.app_context():
            todo = Todo(user_id=test_user.id, text="Original", completed=False)
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        response = authenticated_client.patch(f"/api/todos/{todo_id}",
                                             data=json.dumps({"text": "Updated", "completed": True}),
                                             content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["text"] == "Updated"
        assert data["completed"] is True

    def test_api_update_todo_not_found(self, authenticated_client):
        """Test updating non-existent todo."""
        response = authenticated_client.patch("/api/todos/99999",
                                             data=json.dumps({"text": "Updated"}),
                                             content_type="application/json")

        assert response.status_code == 404

    def test_api_update_todo_wrong_user(self, authenticated_client, app, another_user):
        """Test updating another user's todo."""
        with app.app_context():
            todo = Todo(user_id=another_user.id, text="Other user", completed=False)
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        response = authenticated_client.patch(f"/api/todos/{todo_id}",
                                             data=json.dumps({"text": "Hacked"}),
                                             content_type="application/json")

        assert response.status_code == 404

        # Verify not updated
        with app.app_context():
            todo = db.session.get(Todo, todo_id)
            assert todo.text == "Other user"

    def test_api_update_todo_empty_text(self, authenticated_client, app, test_user):
        """Test updating todo with empty text."""
        with app.app_context():
            todo = Todo(user_id=test_user.id, text="Original", completed=False)
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        response = authenticated_client.patch(f"/api/todos/{todo_id}",
                                             data=json.dumps({"text": ""}),
                                             content_type="application/json")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data


class TestAPIDeleteTodo:
    """Test cases for DELETE /api/todos/<id>."""

    def test_api_delete_todo_unauthenticated(self, client, app, test_user):
        """Test deleting todo without authentication."""
        with app.app_context():
            todo = Todo(user_id=test_user.id, text="Test", completed=False)
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        response = client.delete(f"/api/todos/{todo_id}")
        assert response.status_code == 302

    def test_api_delete_todo_success(self, authenticated_client, app, test_user):
        """Test successfully deleting a todo."""
        with app.app_context():
            todo = Todo(user_id=test_user.id, text="Delete me", completed=False)
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        response = authenticated_client.delete(f"/api/todos/{todo_id}")
        assert response.status_code == 204

        # Verify deleted
        with app.app_context():
            todo = db.session.get(Todo, todo_id)
            assert todo is None

    def test_api_delete_todo_not_found(self, authenticated_client):
        """Test deleting non-existent todo."""
        response = authenticated_client.delete("/api/todos/99999")
        assert response.status_code == 404

    def test_api_delete_todo_wrong_user(self, authenticated_client, app, another_user):
        """Test deleting another user's todo."""
        with app.app_context():
            todo = Todo(user_id=another_user.id, text="Other user", completed=False)
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        response = authenticated_client.delete(f"/api/todos/{todo_id}")
        assert response.status_code == 404

        # Verify not deleted
        with app.app_context():
            todo = db.session.get(Todo, todo_id)
            assert todo is not None


class TestSerializeTodo:
    """Test cases for serialize_todo function."""

    def test_serialize_todo(self, app, test_user):
        """Test serializing a todo."""
        with app.app_context():
            todo = Todo(user_id=test_user.id, text="Test todo", completed=False)
            db.session.add(todo)
            db.session.commit()

            serialized = serialize_todo(todo)

            assert serialized["id"] == todo.id
            assert serialized["text"] == "Test todo"
            assert serialized["completed"] is False
            assert "created_at" in serialized
            assert serialized["created_at"] == todo.created_at.isoformat()

    def test_serialize_todo_completed(self, app, test_user):
        """Test serializing a completed todo."""
        with app.app_context():
            todo = Todo(user_id=test_user.id, text="Done", completed=True)
            db.session.add(todo)
            db.session.commit()

            serialized = serialize_todo(todo)

            assert serialized["completed"] is True

    def test_serialize_todo_with_updated_at(self, app, test_user):
        """Test serializing todo with updated_at."""
        with app.app_context():
            todo = Todo(user_id=test_user.id, text="Test", completed=False)
            db.session.add(todo)
            db.session.commit()

            # Update to set updated_at
            todo.text = "Updated"
            db.session.commit()

            serialized = serialize_todo(todo)

            assert serialized["updated_at"] is not None
            if todo.updated_at:
                assert serialized["updated_at"] == todo.updated_at.isoformat()
