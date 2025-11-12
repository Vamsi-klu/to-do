"""Tests for API endpoints."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
import pytest
from models import Todo


class TestTodoListAPI:
    """Tests for GET /api/todos endpoint."""

    def test_list_todos(self, authenticated_client, user, todo, completed_todo):
        """Test listing todos."""
        response = authenticated_client.get("/api/todos")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "todos" in data
        assert len(data["todos"]) == 2
        assert data["total"] == 2

    def test_list_todos_pagination(self, authenticated_client, user, db):
        """Test pagination of todos."""
        # Create 10 todos
        for i in range(10):
            todo = Todo(user_id=user.id, text=f"Todo {i}", completed=False)
            db.session.add(todo)
        db.session.commit()

        # Get first page
        response = authenticated_client.get("/api/todos?page=1&per_page=5")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["todos"]) == 5
        assert data["total"] == 10
        assert data["pages"] == 2
        assert data["current_page"] == 1

        # Get second page
        response = authenticated_client.get("/api/todos?page=2&per_page=5")
        data = json.loads(response.data)
        assert len(data["todos"]) == 5
        assert data["current_page"] == 2

    def test_filter_by_status_active(self, authenticated_client, user, todo, completed_todo):
        """Test filtering by active status."""
        response = authenticated_client.get("/api/todos?status=active")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["todos"]) == 1
        assert data["todos"][0]["completed"] is False

    def test_filter_by_status_completed(self, authenticated_client, user, todo, completed_todo):
        """Test filtering by completed status."""
        response = authenticated_client.get("/api/todos?status=completed")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["todos"]) == 1
        assert data["todos"][0]["completed"] is True

    def test_search_todos(self, authenticated_client, user, db):
        """Test searching todos by text."""
        todo1 = Todo(user_id=user.id, text="Buy groceries", completed=False)
        todo2 = Todo(user_id=user.id, text="Buy tickets", completed=False)
        todo3 = Todo(user_id=user.id, text="Call dentist", completed=False)
        db.session.add_all([todo1, todo2, todo3])
        db.session.commit()

        response = authenticated_client.get("/api/todos?search=buy")
        data = json.loads(response.data)
        assert len(data["todos"]) == 2

        response = authenticated_client.get("/api/todos?search=dentist")
        data = json.loads(response.data)
        assert len(data["todos"]) == 1

    def test_filter_by_priority(self, authenticated_client, user, db):
        """Test filtering by priority."""
        high_todo = Todo(user_id=user.id, text="High priority", priority="high")
        low_todo = Todo(user_id=user.id, text="Low priority", priority="low")
        db.session.add_all([high_todo, low_todo])
        db.session.commit()

        response = authenticated_client.get("/api/todos?priority=high")
        data = json.loads(response.data)
        assert len(data["todos"]) == 1
        assert data["todos"][0]["priority"] == "high"

    def test_filter_by_category(self, authenticated_client, user, db):
        """Test filtering by category."""
        work_todo = Todo(user_id=user.id, text="Work task", category="work")
        personal_todo = Todo(user_id=user.id, text="Personal task", category="personal")
        db.session.add_all([work_todo, personal_todo])
        db.session.commit()

        response = authenticated_client.get("/api/todos?category=work")
        data = json.loads(response.data)
        assert len(data["todos"]) == 1
        assert data["todos"][0]["category"] == "work"


class TestCreateTodoAPI:
    """Tests for POST /api/todos endpoint."""

    def test_create_todo(self, authenticated_client, user):
        """Test creating a todo."""
        response = authenticated_client.post(
            "/api/todos",
            data=json.dumps({"text": "New todo"}),
            content_type="application/json",
        )
        assert response.status_code == 201

        data = json.loads(response.data)
        assert data["text"] == "New todo"
        assert data["completed"] is False
        assert data["priority"] == "medium"
        assert "id" in data

    def test_create_todo_with_all_fields(self, authenticated_client, user):
        """Test creating a todo with all fields."""
        due_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
        response = authenticated_client.post(
            "/api/todos",
            data=json.dumps({
                "text": "Complete project",
                "priority": "high",
                "category": "work",
                "due_date": due_date,
            }),
            content_type="application/json",
        )
        assert response.status_code == 201

        data = json.loads(response.data)
        assert data["text"] == "Complete project"
        assert data["priority"] == "high"
        assert data["category"] == "work"
        assert data["due_date"] is not None

    def test_create_todo_with_empty_text(self, authenticated_client):
        """Test creating a todo with empty text."""
        response = authenticated_client.post(
            "/api/todos",
            data=json.dumps({"text": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_create_todo_with_invalid_priority(self, authenticated_client):
        """Test creating a todo with invalid priority."""
        response = authenticated_client.post(
            "/api/todos",
            data=json.dumps({"text": "Test", "priority": "urgent"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_create_todo_with_invalid_due_date(self, authenticated_client):
        """Test creating a todo with invalid due date."""
        response = authenticated_client.post(
            "/api/todos",
            data=json.dumps({"text": "Test", "due_date": "invalid-date"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data


class TestUpdateTodoAPI:
    """Tests for PATCH /api/todos/<id> endpoint."""

    def test_update_todo_text(self, authenticated_client, todo):
        """Test updating todo text."""
        response = authenticated_client.patch(
            f"/api/todos/{todo.id}",
            data=json.dumps({"text": "Updated text"}),
            content_type="application/json",
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["text"] == "Updated text"

    def test_update_todo_completed_status(self, authenticated_client, todo):
        """Test updating todo completed status."""
        assert todo.completed is False

        response = authenticated_client.patch(
            f"/api/todos/{todo.id}",
            data=json.dumps({"completed": True}),
            content_type="application/json",
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["completed"] is True

    def test_update_todo_priority(self, authenticated_client, todo):
        """Test updating todo priority."""
        response = authenticated_client.patch(
            f"/api/todos/{todo.id}",
            data=json.dumps({"priority": "high"}),
            content_type="application/json",
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["priority"] == "high"

    def test_update_todo_category(self, authenticated_client, todo):
        """Test updating todo category."""
        response = authenticated_client.patch(
            f"/api/todos/{todo.id}",
            data=json.dumps({"category": "work"}),
            content_type="application/json",
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["category"] == "work"

    def test_update_todo_due_date(self, authenticated_client, todo):
        """Test updating todo due date."""
        due_date = (datetime.utcnow() + timedelta(days=2)).isoformat()
        response = authenticated_client.patch(
            f"/api/todos/{todo.id}",
            data=json.dumps({"due_date": due_date}),
            content_type="application/json",
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["due_date"] is not None

    def test_update_nonexistent_todo(self, authenticated_client):
        """Test updating a non-existent todo."""
        response = authenticated_client.patch(
            "/api/todos/99999",
            data=json.dumps({"text": "Updated"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_update_todo_with_invalid_data(self, authenticated_client, todo):
        """Test updating todo with invalid data."""
        response = authenticated_client.patch(
            f"/api/todos/{todo.id}",
            data=json.dumps({"text": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400


class TestDeleteTodoAPI:
    """Tests for DELETE /api/todos/<id> endpoint."""

    def test_delete_todo(self, authenticated_client, todo, db):
        """Test deleting a todo."""
        todo_id = todo.id

        response = authenticated_client.delete(f"/api/todos/{todo_id}")
        assert response.status_code == 204

        # Todo should be deleted
        deleted_todo = db.session.get(Todo, todo_id)
        assert deleted_todo is None

    def test_delete_nonexistent_todo(self, authenticated_client):
        """Test deleting a non-existent todo."""
        response = authenticated_client.delete("/api/todos/99999")
        assert response.status_code == 404


class TestUserProfileAPI:
    """Tests for user profile API endpoints."""

    def test_get_profile(self, authenticated_client, user):
        """Test getting user profile."""
        response = authenticated_client.get("/api/user/profile")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["username"] == user.username
        assert data["id"] == user.id
        assert "created_at" in data

    def test_change_password(self, authenticated_client, user):
        """Test changing password."""
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

        # Verify password was changed
        assert user.check_password("NewPassword123") is True

    def test_change_password_wrong_current(self, authenticated_client):
        """Test changing password with wrong current password."""
        response = authenticated_client.post(
            "/api/user/change-password",
            data=json.dumps({
                "current_password": "WrongPassword",
                "new_password": "NewPassword123",
                "confirm_password": "NewPassword123",
            }),
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_change_password_mismatch(self, authenticated_client):
        """Test changing password with mismatched new passwords."""
        response = authenticated_client.post(
            "/api/user/change-password",
            data=json.dumps({
                "current_password": "Test123456",
                "new_password": "NewPassword123",
                "confirm_password": "DifferentPassword123",
            }),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_delete_account(self, authenticated_client, user, db):
        """Test deleting user account."""
        user_id = user.id

        response = authenticated_client.delete(
            "/api/user/account",
            data=json.dumps({"password": "Test123456"}),
            content_type="application/json",
        )
        assert response.status_code == 200

        # User should be deleted
        from models import User
        deleted_user = db.session.get(User, user_id)
        assert deleted_user is None

    def test_delete_account_wrong_password(self, authenticated_client):
        """Test deleting account with wrong password."""
        response = authenticated_client.delete(
            "/api/user/account",
            data=json.dumps({"password": "WrongPassword"}),
            content_type="application/json",
        )
        assert response.status_code == 401


class TestStatsAPI:
    """Tests for stats API endpoint."""

    def test_get_stats(self, authenticated_client, user, db):
        """Test getting user statistics."""
        # Create some todos
        todo1 = Todo(user_id=user.id, text="Active", completed=False, priority="high")
        todo2 = Todo(user_id=user.id, text="Completed", completed=True)
        overdue_date = datetime.utcnow() - timedelta(days=1)
        todo3 = Todo(
            user_id=user.id,
            text="Overdue",
            completed=False,
            due_date=overdue_date,
            priority="high"
        )
        db.session.add_all([todo1, todo2, todo3])
        db.session.commit()

        response = authenticated_client.get("/api/stats")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["total"] == 3
        assert data["completed"] == 1
        assert data["active"] == 2
        assert data["overdue"] == 1
        assert data["high_priority"] == 2
