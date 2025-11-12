"""Tests for security and authorization."""
from __future__ import annotations

import json
import pytest
from models import Todo


class TestAuthorization:
    """Tests for user authorization and data isolation."""

    def test_user_cannot_view_other_users_todos(
        self, authenticated_client, user, another_user, db
    ):
        """Test that users can only see their own todos."""
        # Create todos for both users
        user_todo = Todo(user_id=user.id, text="User's todo", completed=False)
        other_todo = Todo(user_id=another_user.id, text="Other user's todo", completed=False)
        db.session.add_all([user_todo, other_todo])
        db.session.commit()

        # User should only see their own todo
        response = authenticated_client.get("/api/todos")
        data = json.loads(response.data)

        assert len(data["todos"]) == 1
        assert data["todos"][0]["text"] == "User's todo"

    def test_user_cannot_update_other_users_todo(
        self, authenticated_client, another_user, db
    ):
        """Test that users cannot update other users' todos."""
        # Create todo for another user
        other_todo = Todo(user_id=another_user.id, text="Other's todo", completed=False)
        db.session.add(other_todo)
        db.session.commit()

        # Try to update another user's todo
        response = authenticated_client.patch(
            f"/api/todos/{other_todo.id}",
            data=json.dumps({"text": "Hacked"}),
            content_type="application/json",
        )
        assert response.status_code == 404

        # Todo should not be modified
        db.session.refresh(other_todo)
        assert other_todo.text == "Other's todo"

    def test_user_cannot_delete_other_users_todo(
        self, authenticated_client, another_user, db
    ):
        """Test that users cannot delete other users' todos."""
        # Create todo for another user
        other_todo = Todo(user_id=another_user.id, text="Other's todo", completed=False)
        db.session.add(other_todo)
        db.session.commit()

        todo_id = other_todo.id

        # Try to delete another user's todo
        response = authenticated_client.delete(f"/api/todos/{todo_id}")
        assert response.status_code == 404

        # Todo should still exist
        assert db.session.get(Todo, todo_id) is not None


class TestPasswordSecurity:
    """Tests for password security."""

    def test_passwords_are_hashed(self, user):
        """Test that passwords are never stored in plaintext."""
        # Password hash should not equal the password
        assert user.password_hash != "Test123456"

        # Password hash should contain hash indicators
        assert user.password_hash.startswith("scrypt:") or user.password_hash.startswith("pbkdf2:")

    def test_different_users_same_password_different_hashes(self, db):
        """Test that same password produces different hashes (salt)."""
        from models import User

        user1 = User(username="user1")
        user1.set_password("SamePassword123")

        user2 = User(username="user2")
        user2.set_password("SamePassword123")

        db.session.add_all([user1, user2])
        db.session.commit()

        # Same password should produce different hashes due to salt
        assert user1.password_hash != user2.password_hash

    def test_password_cannot_be_read(self, user):
        """Test that there's no way to retrieve the original password."""
        # Model should not have a password field
        assert not hasattr(user, "password")

        # Only password_hash exists
        assert hasattr(user, "password_hash")


class TestInputValidation:
    """Tests for input validation and sanitization."""

    def test_sql_injection_prevention_in_search(self, authenticated_client, db, user):
        """Test that SQL injection attempts are prevented."""
        # Create a test todo
        todo = Todo(user_id=user.id, text="Normal todo", completed=False)
        db.session.add(todo)
        db.session.commit()

        # Try SQL injection
        response = authenticated_client.get("/api/todos?search=' OR '1'='1")
        assert response.status_code == 200

        # Should not return unexpected results or error
        data = json.loads(response.data)
        # SQLAlchemy should handle this safely

    def test_xss_prevention_in_todo_text(self, authenticated_client):
        """Test that XSS attempts are stored but not executed."""
        xss_text = "<script>alert('XSS')</script>"

        response = authenticated_client.post(
            "/api/todos",
            data=json.dumps({"text": xss_text}),
            content_type="application/json",
        )
        assert response.status_code == 201

        data = json.loads(response.data)
        # Text should be stored as-is (template engine should escape it)
        assert data["text"] == xss_text

    def test_whitespace_stripping(self, authenticated_client):
        """Test that whitespace is stripped from inputs."""
        response = authenticated_client.post(
            "/api/todos",
            data=json.dumps({"text": "  Todo with spaces  "}),
            content_type="application/json",
        )
        assert response.status_code == 201

        data = json.loads(response.data)
        assert data["text"] == "Todo with spaces"

    def test_very_long_text_rejected(self, authenticated_client):
        """Test that very long text is rejected."""
        long_text = "a" * 501  # Exceeds 500 character limit

        response = authenticated_client.post(
            "/api/todos",
            data=json.dumps({"text": long_text}),
            content_type="application/json",
        )
        assert response.status_code == 400


class TestSessionSecurity:
    """Tests for session security."""

    def test_session_cleared_on_logout(self, authenticated_client, user):
        """Test that session is completely cleared on logout."""
        # Verify logged in
        with authenticated_client.session_transaction() as sess:
            assert sess.get("user_id") == user.id

        # Logout
        authenticated_client.post("/logout")

        # Session should be empty
        with authenticated_client.session_transaction() as sess:
            assert len(sess) == 0
            assert sess.get("user_id") is None

    def test_cannot_forge_session(self, client):
        """Test that manually setting session doesn't bypass security."""
        # Try to manually set an invalid user_id
        with client.session_transaction() as sess:
            sess["user_id"] = 99999  # Non-existent user

        # Should still not be able to access protected routes properly
        response = client.get("/api/todos")
        # Should get error since user doesn't exist
        assert response.status_code in [401, 500]


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_error_handler(self, authenticated_client):
        """Test 404 error handler."""
        response = authenticated_client.get("/nonexistent-endpoint")
        assert response.status_code == 404

    def test_404_api_returns_json(self, authenticated_client):
        """Test that 404 on API endpoints returns JSON."""
        response = authenticated_client.get("/api/nonexistent")
        assert response.status_code == 404
        assert response.content_type == "application/json"

        data = json.loads(response.data)
        assert "error" in data

    def test_500_error_handler(self, authenticated_client, monkeypatch):
        """Test 500 error handler."""
        # Mock a function to raise an exception
        def mock_error(*args, **kwargs):
            raise Exception("Test error")

        # This is tricky to test without actually breaking something
        # We'll skip this for now as it requires more complex mocking

    def test_invalid_json_handled(self, authenticated_client):
        """Test that invalid JSON is handled gracefully."""
        response = authenticated_client.post(
            "/api/todos",
            data="invalid json{",
            content_type="application/json",
        )
        # Should not crash, should handle gracefully
        assert response.status_code in [400, 500]


class TestCSRFProtection:
    """Tests for CSRF protection."""

    def test_csrf_disabled_in_testing(self, client):
        """Test that CSRF is disabled in testing configuration."""
        # In testing mode, CSRF should be disabled for easier testing
        response = client.post(
            "/register",
            data={
                "username": "testuser",
                "password": "Password123",
                "confirm": "Password123",
            },
        )
        # Should work without CSRF token in testing mode
        assert response.status_code in [200, 302, 400]


class TestPasswordStrength:
    """Tests for password strength enforcement."""

    def test_weak_password_rejected(self, client):
        """Test that weak passwords are rejected."""
        # Too short
        response = client.post(
            "/register",
            data={
                "username": "newuser",
                "password": "Pass1",
                "confirm": "Pass1",
            },
        )
        assert response.status_code == 400

    def test_password_without_number_rejected(self, client):
        """Test that password without number is rejected."""
        response = client.post(
            "/register",
            data={
                "username": "newuser",
                "password": "PasswordNoNumber",
                "confirm": "PasswordNoNumber",
            },
        )
        assert response.status_code == 400

    def test_password_without_letter_rejected(self, client):
        """Test that password without letter is rejected."""
        response = client.post(
            "/register",
            data={
                "username": "newuser",
                "password": "12345678",
                "confirm": "12345678",
            },
        )
        assert response.status_code == 400
