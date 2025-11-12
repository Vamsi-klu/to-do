"""Integration tests for complete workflows."""
from __future__ import annotations

import json
from datetime import datetime, timedelta


class TestCompleteUserWorkflow:
    """Integration tests for complete user workflows."""

    def test_user_registration_and_login_workflow(self, client, db):
        """Test complete user registration and login workflow."""
        # Step 1: Register a new user
        response = client.post(
            "/register",
            data={
                "username": "newuser",
                "password": "NewUser123",
                "confirm": "NewUser123",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302

        # Step 2: User should be logged in automatically after registration
        with client.session_transaction() as sess:
            assert sess.get("user_id") is not None

        # Step 3: Logout
        response = client.post("/logout", follow_redirects=False)
        assert response.status_code == 302

        # Step 4: Login with the new account
        response = client.post(
            "/login",
            data={"username": "newuser", "password": "NewUser123"},
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Step 5: Access protected page
        response = client.get("/")
        assert response.status_code == 200

    def test_complete_todo_lifecycle(self, authenticated_client, user):
        """Test complete todo lifecycle: create, read, update, delete."""
        # Step 1: Create a todo
        response = authenticated_client.post(
            "/api/todos",
            data=json.dumps({
                "text": "Buy groceries",
                "priority": "high",
                "category": "shopping",
            }),
            content_type="application/json",
        )
        assert response.status_code == 201
        created_todo = json.loads(response.data)
        todo_id = created_todo["id"]

        # Step 2: List todos and verify it appears
        response = authenticated_client.get("/api/todos")
        data = json.loads(response.data)
        assert len(data["todos"]) == 1
        assert data["todos"][0]["text"] == "Buy groceries"

        # Step 3: Update the todo
        response = authenticated_client.patch(
            f"/api/todos/{todo_id}",
            data=json.dumps({
                "text": "Buy groceries and milk",
                "completed": True,
            }),
            content_type="application/json",
        )
        assert response.status_code == 200
        updated_todo = json.loads(response.data)
        assert updated_todo["text"] == "Buy groceries and milk"
        assert updated_todo["completed"] is True

        # Step 4: Delete the todo
        response = authenticated_client.delete(f"/api/todos/{todo_id}")
        assert response.status_code == 204

        # Step 5: Verify todo is deleted
        response = authenticated_client.get("/api/todos")
        data = json.loads(response.data)
        assert len(data["todos"]) == 0

    def test_multiple_todos_workflow(self, authenticated_client, user):
        """Test managing multiple todos with different states."""
        # Create multiple todos
        todos = [
            {"text": "Work task", "priority": "high", "category": "work"},
            {"text": "Personal task", "priority": "low", "category": "personal"},
            {"text": "Shopping task", "priority": "medium", "category": "shopping"},
        ]

        created_ids = []
        for todo_data in todos:
            response = authenticated_client.post(
                "/api/todos",
                data=json.dumps(todo_data),
                content_type="application/json",
            )
            assert response.status_code == 201
            created_ids.append(json.loads(response.data)["id"])

        # List all todos
        response = authenticated_client.get("/api/todos")
        data = json.loads(response.data)
        assert len(data["todos"]) == 3

        # Complete one todo
        authenticated_client.patch(
            f"/api/todos/{created_ids[0]}",
            data=json.dumps({"completed": True}),
            content_type="application/json",
        )

        # Filter by status
        response = authenticated_client.get("/api/todos?status=active")
        data = json.loads(response.data)
        assert len(data["todos"]) == 2

        response = authenticated_client.get("/api/todos?status=completed")
        data = json.loads(response.data)
        assert len(data["todos"]) == 1

        # Filter by category
        response = authenticated_client.get("/api/todos?category=work")
        data = json.loads(response.data)
        assert len(data["todos"]) == 1

        # Search
        response = authenticated_client.get("/api/todos?search=task")
        data = json.loads(response.data)
        assert len(data["todos"]) == 3

    def test_user_profile_management_workflow(self, authenticated_client, user, db):
        """Test user profile management workflow."""
        # Step 1: Get profile
        response = authenticated_client.get("/api/user/profile")
        assert response.status_code == 200
        profile = json.loads(response.data)
        assert profile["username"] == "testuser"

        # Step 2: Change password
        response = authenticated_client.post(
            "/api/user/change-password",
            data=json.dumps({
                "current_password": "Test123456",
                "new_password": "NewPassword123",
                "confirm_password": "NewPassword123",
            }),
            content_type="application/json",
        )
        assert response.status_code == 200

        # Step 3: Logout
        authenticated_client.post("/logout")

        # Step 4: Login with new password
        response = authenticated_client.post(
            "/login",
            data={"username": "testuser", "password": "NewPassword123"},
        )
        assert response.status_code == 302

    def test_todo_with_due_date_workflow(self, authenticated_client, user, db):
        """Test managing todos with due dates."""
        # Create todo with due date in future
        future_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
        response = authenticated_client.post(
            "/api/todos",
            data=json.dumps({
                "text": "Complete project",
                "due_date": future_date,
                "priority": "high",
            }),
            content_type="application/json",
        )
        assert response.status_code == 201
        todo = json.loads(response.data)
        assert todo["is_overdue"] is False

        # Create overdue todo
        past_date = (datetime.utcnow() - timedelta(days=1)).isoformat()
        response = authenticated_client.post(
            "/api/todos",
            data=json.dumps({
                "text": "Overdue task",
                "due_date": past_date,
                "priority": "high",
            }),
            content_type="application/json",
        )
        assert response.status_code == 201
        todo = json.loads(response.data)
        assert todo["is_overdue"] is True

        # Check stats
        response = authenticated_client.get("/api/stats")
        stats = json.loads(response.data)
        assert stats["overdue"] == 1


class TestMultiUserWorkflow:
    """Integration tests involving multiple users."""

    def test_multiple_users_data_isolation(self, client, db):
        """Test that multiple users have isolated data."""
        # Register first user
        client.post(
            "/register",
            data={
                "username": "user1",
                "password": "User1Pass123",
                "confirm": "User1Pass123",
            },
        )

        # Create todo for user1
        client.post(
            "/api/todos",
            data=json.dumps({"text": "User1's todo"}),
            content_type="application/json",
        )

        # Logout
        client.post("/logout")

        # Register second user
        client.post(
            "/register",
            data={
                "username": "user2",
                "password": "User2Pass123",
                "confirm": "User2Pass123",
            },
        )

        # Create todo for user2
        client.post(
            "/api/todos",
            data=json.dumps({"text": "User2's todo"}),
            content_type="application/json",
        )

        # User2 should only see their todo
        response = client.get("/api/todos")
        data = json.loads(response.data)
        assert len(data["todos"]) == 1
        assert data["todos"][0]["text"] == "User2's todo"

        # Logout and login as user1
        client.post("/logout")
        client.post(
            "/login",
            data={"username": "user1", "password": "User1Pass123"},
        )

        # User1 should only see their todo
        response = client.get("/api/todos")
        data = json.loads(response.data)
        assert len(data["todos"]) == 1
        assert data["todos"][0]["text"] == "User1's todo"


class TestErrorRecoveryWorkflow:
    """Integration tests for error handling and recovery."""

    def test_invalid_operations_dont_corrupt_state(self, authenticated_client, db):
        """Test that failed operations don't corrupt application state."""
        # Create a valid todo
        response = authenticated_client.post(
            "/api/todos",
            data=json.dumps({"text": "Valid todo"}),
            content_type="application/json",
        )
        assert response.status_code == 201
        todo_id = json.loads(response.data)["id"]

        # Try to update with invalid data
        response = authenticated_client.patch(
            f"/api/todos/{todo_id}",
            data=json.dumps({"text": ""}),  # Invalid empty text
            content_type="application/json",
        )
        assert response.status_code == 400

        # Original todo should still exist unchanged
        response = authenticated_client.get("/api/todos")
        data = json.loads(response.data)
        assert len(data["todos"]) == 1
        assert data["todos"][0]["text"] == "Valid todo"

    def test_session_persistence_across_requests(self, authenticated_client, user):
        """Test that session persists across multiple requests."""
        # Make multiple requests
        for _ in range(5):
            response = authenticated_client.get("/api/todos")
            assert response.status_code == 200

        # Session should still be valid
        with authenticated_client.session_transaction() as sess:
            assert sess.get("user_id") == user.id


class TestPaginationWorkflow:
    """Integration tests for pagination."""

    def test_pagination_with_filters(self, authenticated_client, user, db):
        """Test pagination works with filters."""
        from models import Todo

        # Create 25 todos
        for i in range(25):
            priority = "high" if i < 10 else "low"
            todo = Todo(
                user_id=user.id,
                text=f"Todo {i}",
                priority=priority,
                completed=(i % 2 == 0),
            )
            db.session.add(todo)
        db.session.commit()

        # Test pagination
        response = authenticated_client.get("/api/todos?page=1&per_page=10")
        data = json.loads(response.data)
        assert len(data["todos"]) == 10
        assert data["pages"] == 3

        # Test pagination with filter
        response = authenticated_client.get(
            "/api/todos?page=1&per_page=10&priority=high"
        )
        data = json.loads(response.data)
        assert len(data["todos"]) == 10
        assert all(t["priority"] == "high" for t in data["todos"])

        # Test pagination with status filter
        response = authenticated_client.get(
            "/api/todos?page=1&per_page=10&status=active"
        )
        data = json.loads(response.data)
        assert all(not t["completed"] for t in data["todos"])
