"""Integration tests for complete user workflows."""
from __future__ import annotations

import json

import pytest

from database import db
from models import User, Todo


class TestAuthenticationFlow:
    """Integration tests for complete authentication workflows."""

    def test_full_registration_login_logout_flow(self, client, app):
        """Test complete registration -> login -> logout flow."""
        # Register a new user
        response = client.post("/register", data={
            "username": "integrationuser",
            "password": "testpass123",
            "confirm": "testpass123"
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"Your Tasks" in response.data  # Redirected to index

        # Verify user exists in database
        with app.app_context():
            user = User.query.filter_by(username="integrationuser").first()
            assert user is not None
            assert user.check_password("testpass123")
            user_id = user.id

        # Logout
        response = client.post("/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"Welcome back" in response.data  # Redirected to login

        # Login again
        response = client.post("/login", data={
            "username": "integrationuser",
            "password": "testpass123"
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"Your Tasks" in response.data

        # Verify session
        with client.session_transaction() as sess:
            assert sess.get("user_id") == user_id

    def test_registration_with_immediate_todo_creation(self, client, app):
        """Test registering and immediately creating a todo."""
        # Register
        response = client.post("/register", data={
            "username": "todouser",
            "password": "pass123",
            "confirm": "pass123"
        }, follow_redirects=True)

        assert response.status_code == 200

        # Create a todo
        response = client.post("/api/todos",
                              data=json.dumps({"text": "First todo after registration"}),
                              content_type="application/json")

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["text"] == "First todo after registration"

        # Verify in database
        with app.app_context():
            user = User.query.filter_by(username="todouser").first()
            assert len(user.todos) == 1
            assert user.todos[0].text == "First todo after registration"

    def test_failed_login_attempts(self, client, test_user):
        """Test multiple failed login attempts."""
        # First failed attempt
        response = client.post("/login", data={
            "username": "testuser",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        assert b"Invalid credentials" in response.data

        # Second failed attempt
        response = client.post("/login", data={
            "username": "testuser",
            "password": "wrongpass2"
        })
        assert response.status_code == 401

        # Successful attempt
        response = client.post("/login", data={
            "username": "testuser",
            "password": "testpass123"
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"Your Tasks" in response.data

    def test_session_persistence_across_requests(self, client, test_user):
        """Test that session persists across multiple requests."""
        # Login
        client.post("/login", data={
            "username": "testuser",
            "password": "testpass123"
        })

        # Make multiple requests
        for _ in range(5):
            response = client.get("/")
            assert response.status_code == 200
            assert b"Your Tasks" in response.data

    def test_protected_routes_without_login(self, client):
        """Test accessing protected routes without login."""
        # Try to access index
        response = client.get("/")
        assert response.status_code == 302
        assert "/login" in response.location

        # Try to access API
        response = client.get("/api/todos")
        assert response.status_code == 302

        response = client.post("/api/todos",
                              data=json.dumps({"text": "Test"}),
                              content_type="application/json")
        assert response.status_code == 302


class TestTodoCRUDFlow:
    """Integration tests for complete todo CRUD workflows."""

    def test_full_todo_lifecycle(self, authenticated_client, app, test_user):
        """Test creating, reading, updating, and deleting a todo."""
        # Create todo
        response = authenticated_client.post("/api/todos",
                                            data=json.dumps({"text": "Lifecycle test"}),
                                            content_type="application/json")
        assert response.status_code == 201
        todo_data = json.loads(response.data)
        todo_id = todo_data["id"]

        # Read todos (list)
        response = authenticated_client.get("/api/todos")
        assert response.status_code == 200
        todos = json.loads(response.data)
        assert len(todos) == 1
        assert todos[0]["id"] == todo_id
        assert todos[0]["text"] == "Lifecycle test"
        assert todos[0]["completed"] is False

        # Update todo text
        response = authenticated_client.patch(f"/api/todos/{todo_id}",
                                             data=json.dumps({"text": "Updated lifecycle test"}),
                                             content_type="application/json")
        assert response.status_code == 200
        updated_data = json.loads(response.data)
        assert updated_data["text"] == "Updated lifecycle test"

        # Update todo completed status
        response = authenticated_client.patch(f"/api/todos/{todo_id}",
                                             data=json.dumps({"completed": True}),
                                             content_type="application/json")
        assert response.status_code == 200
        updated_data = json.loads(response.data)
        assert updated_data["completed"] is True

        # Delete todo
        response = authenticated_client.delete(f"/api/todos/{todo_id}")
        assert response.status_code == 204

        # Verify deleted
        response = authenticated_client.get("/api/todos")
        todos = json.loads(response.data)
        assert len(todos) == 0

    def test_multiple_todos_workflow(self, authenticated_client, app):
        """Test managing multiple todos."""
        # Create multiple todos
        todos_to_create = ["Buy groceries", "Write code", "Exercise", "Read book"]
        created_ids = []

        for text in todos_to_create:
            response = authenticated_client.post("/api/todos",
                                                data=json.dumps({"text": text}),
                                                content_type="application/json")
            assert response.status_code == 201
            data = json.loads(response.data)
            created_ids.append(data["id"])

        # List all todos
        response = authenticated_client.get("/api/todos")
        todos = json.loads(response.data)
        assert len(todos) == len(todos_to_create)

        # Complete some todos
        for i in [0, 2]:  # Complete first and third
            response = authenticated_client.patch(f"/api/todos/{created_ids[i]}",
                                                 data=json.dumps({"completed": True}),
                                                 content_type="application/json")
            assert response.status_code == 200

        # Verify completed status
        response = authenticated_client.get("/api/todos")
        todos = json.loads(response.data)
        completed_count = sum(1 for t in todos if t["completed"])
        assert completed_count == 2

        # Delete completed todos
        with app.app_context():
            completed = Todo.query.filter_by(completed=True).all()
            for todo in completed:
                response = authenticated_client.delete(f"/api/todos/{todo.id}")
                assert response.status_code == 204

        # Verify remaining todos
        response = authenticated_client.get("/api/todos")
        todos = json.loads(response.data)
        assert len(todos) == 2

    def test_todo_isolation_between_users(self, client, app, test_user, another_user):
        """Test that todos are properly isolated between users."""
        # Login as first user
        client.post("/login", data={
            "username": "testuser",
            "password": "testpass123"
        })

        # Create todos for first user
        client.post("/api/todos",
                   data=json.dumps({"text": "User 1 Todo 1"}),
                   content_type="application/json")
        client.post("/api/todos",
                   data=json.dumps({"text": "User 1 Todo 2"}),
                   content_type="application/json")

        # Get first user's todos
        response = client.get("/api/todos")
        user1_todos = json.loads(response.data)
        assert len(user1_todos) == 2

        # Logout
        client.post("/logout")

        # Login as second user
        client.post("/login", data={
            "username": "anotheruser",
            "password": "anotherpass123"
        })

        # Second user should have no todos
        response = client.get("/api/todos")
        user2_todos = json.loads(response.data)
        assert len(user2_todos) == 0

        # Create todos for second user
        client.post("/api/todos",
                   data=json.dumps({"text": "User 2 Todo 1"}),
                   content_type="application/json")

        # Get second user's todos
        response = client.get("/api/todos")
        user2_todos = json.loads(response.data)
        assert len(user2_todos) == 1
        assert user2_todos[0]["text"] == "User 2 Todo 1"

        # Verify first user still has their todos
        client.post("/logout")
        client.post("/login", data={
            "username": "testuser",
            "password": "testpass123"
        })

        response = client.get("/api/todos")
        user1_todos = json.loads(response.data)
        assert len(user1_todos) == 2

    def test_concurrent_todo_operations(self, authenticated_client, app):
        """Test multiple operations in quick succession."""
        # Rapidly create todos
        todo_ids = []
        for i in range(10):
            response = authenticated_client.post("/api/todos",
                                                data=json.dumps({"text": f"Todo {i}"}),
                                                content_type="application/json")
            assert response.status_code == 201
            data = json.loads(response.data)
            todo_ids.append(data["id"])

        # Rapidly update todos
        for todo_id in todo_ids[:5]:
            response = authenticated_client.patch(f"/api/todos/{todo_id}",
                                                 data=json.dumps({"completed": True}),
                                                 content_type="application/json")
            assert response.status_code == 200

        # Rapidly delete todos
        for todo_id in todo_ids[5:]:
            response = authenticated_client.delete(f"/api/todos/{todo_id}")
            assert response.status_code == 204

        # Verify final state
        response = authenticated_client.get("/api/todos")
        todos = json.loads(response.data)
        assert len(todos) == 5
        assert all(t["completed"] for t in todos)

    def test_error_recovery_workflow(self, authenticated_client, app, test_user):
        """Test recovering from errors during operations."""
        # Create a valid todo
        response = authenticated_client.post("/api/todos",
                                            data=json.dumps({"text": "Valid todo"}),
                                            content_type="application/json")
        assert response.status_code == 201
        todo_id = json.loads(response.data)["id"]

        # Try to update with invalid data
        response = authenticated_client.patch(f"/api/todos/{todo_id}",
                                             data=json.dumps({"text": ""}),
                                             content_type="application/json")
        assert response.status_code == 400

        # Verify todo is unchanged
        response = authenticated_client.get("/api/todos")
        todos = json.loads(response.data)
        assert len(todos) == 1
        assert todos[0]["text"] == "Valid todo"

        # Successfully update
        response = authenticated_client.patch(f"/api/todos/{todo_id}",
                                             data=json.dumps({"text": "Updated todo"}),
                                             content_type="application/json")
        assert response.status_code == 200

        # Verify update
        response = authenticated_client.get("/api/todos")
        todos = json.loads(response.data)
        assert todos[0]["text"] == "Updated todo"


class TestCompleteUserJourney:
    """Integration tests for complete user journeys."""

    def test_new_user_first_day_journey(self, client, app):
        """Test a complete journey of a new user's first day."""
        # 1. User visits the app and registers
        response = client.get("/")
        assert response.status_code == 302  # Redirects to login

        response = client.get("/login")
        assert response.status_code == 200

        response = client.get("/register")
        assert response.status_code == 200

        response = client.post("/register", data={
            "username": "newjourney",
            "password": "journey123",
            "confirm": "journey123"
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"Your Tasks" in response.data

        # 2. User creates their first todos
        morning_tasks = ["Check emails", "Team standup", "Review PRs"]
        for task in morning_tasks:
            response = client.post("/api/todos",
                                  data=json.dumps({"text": task}),
                                  content_type="application/json")
            assert response.status_code == 201

        # 3. User lists their todos
        response = client.get("/api/todos")
        todos = json.loads(response.data)
        assert len(todos) == 3

        # 4. User completes some tasks
        response = client.get("/api/todos")
        todos = json.loads(response.data)

        for todo in todos[:2]:  # Complete first two
            response = client.patch(f"/api/todos/{todo['id']}",
                                   data=json.dumps({"completed": True}),
                                   content_type="application/json")
            assert response.status_code == 200

        # 5. User adds afternoon tasks
        afternoon_tasks = ["Lunch meeting", "Code review", "Deploy to staging"]
        for task in afternoon_tasks:
            response = client.post("/api/todos",
                                  data=json.dumps({"text": task}),
                                  content_type="application/json")
            assert response.status_code == 201

        # 6. User reviews their day
        response = client.get("/api/todos")
        todos = json.loads(response.data)
        assert len(todos) == 6
        completed_count = sum(1 for t in todos if t["completed"])
        assert completed_count == 2

        # 7. User logs out
        response = client.post("/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"Welcome back" in response.data

        # 8. User logs back in the next day
        response = client.post("/login", data={
            "username": "newjourney",
            "password": "journey123"
        }, follow_redirects=True)
        assert response.status_code == 200

        # 9. User's todos are still there
        response = client.get("/api/todos")
        todos = json.loads(response.data)
        assert len(todos) == 6

    def test_user_data_persistence_across_sessions(self, client, app):
        """Test that user data persists across multiple sessions."""
        # First session: Register and create todos
        client.post("/register", data={
            "username": "persistent",
            "password": "persist123",
            "confirm": "persist123"
        })

        client.post("/api/todos",
                   data=json.dumps({"text": "Persistent todo"}),
                   content_type="application/json")

        response = client.get("/api/todos")
        original_todos = json.loads(response.data)

        client.post("/logout")

        # Second session: Login and verify data
        client.post("/login", data={
            "username": "persistent",
            "password": "persist123"
        })

        response = client.get("/api/todos")
        persisted_todos = json.loads(response.data)

        assert len(persisted_todos) == len(original_todos)
        assert persisted_todos[0]["text"] == original_todos[0]["text"]

    def test_multiple_users_concurrent_usage(self, client, app):
        """Test multiple users using the app concurrently."""
        # Create two users
        users = [
            {"username": "user1", "password": "pass1"},
            {"username": "user2", "password": "pass2"}
        ]

        for user in users:
            client.post("/register", data={
                "username": user["username"],
                "password": user["password"],
                "confirm": user["password"]
            })
            client.post("/logout")

        # User 1 creates todos
        client.post("/login", data=users[0])
        client.post("/api/todos",
                   data=json.dumps({"text": "User 1 todo"}),
                   content_type="application/json")
        client.post("/logout")

        # User 2 creates todos
        client.post("/login", data=users[1])
        client.post("/api/todos",
                   data=json.dumps({"text": "User 2 todo"}),
                   content_type="application/json")

        # Verify User 2 only sees their todos
        response = client.get("/api/todos")
        todos = json.loads(response.data)
        assert len(todos) == 1
        assert todos[0]["text"] == "User 2 todo"

        client.post("/logout")

        # Verify User 1 still has their todos
        client.post("/login", data=users[0])
        response = client.get("/api/todos")
        todos = json.loads(response.data)
        assert len(todos) == 1
        assert todos[0]["text"] == "User 1 todo"
