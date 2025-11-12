"""Tests for authentication and authorization."""
from __future__ import annotations

import pytest
from models import User


class TestLogin:
    """Tests for login functionality."""

    def test_login_page_loads(self, client):
        """Test that login page loads."""
        response = client.get("/login")
        assert response.status_code == 200
        assert b"login" in response.data.lower()

    def test_successful_login(self, client, user):
        """Test successful login."""
        response = client.post(
            "/login",
            data={"username": "testuser", "password": "Test123456"},
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Check session
        with client.session_transaction() as sess:
            assert sess.get("user_id") == user.id

    def test_login_with_wrong_password(self, client, user):
        """Test login with wrong password."""
        response = client.post(
            "/login",
            data={"username": "testuser", "password": "WrongPassword"},
        )
        assert response.status_code == 401
        assert b"Invalid credentials" in response.data

        # Session should not be set
        with client.session_transaction() as sess:
            assert sess.get("user_id") is None

    def test_login_with_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/login",
            data={"username": "nonexistent", "password": "password123"},
        )
        assert response.status_code == 401
        assert b"Invalid credentials" in response.data

    def test_login_with_missing_username(self, client):
        """Test login with missing username."""
        response = client.post(
            "/login",
            data={"password": "password123"},
        )
        assert response.status_code == 400
        assert b"required" in response.data.lower()

    def test_login_with_missing_password(self, client, user):
        """Test login with missing password."""
        response = client.post(
            "/login",
            data={"username": "testuser"},
        )
        assert response.status_code == 400
        assert b"required" in response.data.lower()

    def test_login_redirects_if_already_logged_in(self, authenticated_client):
        """Test that logged-in users are redirected from login page."""
        response = authenticated_client.get("/login", follow_redirects=False)
        assert response.status_code == 302
        assert response.location == "/"


class TestRegister:
    """Tests for registration functionality."""

    def test_register_page_loads(self, client):
        """Test that register page loads."""
        response = client.get("/register")
        assert response.status_code == 200
        assert b"register" in response.data.lower()

    def test_successful_registration(self, client, db):
        """Test successful user registration."""
        response = client.post(
            "/register",
            data={
                "username": "newuser",
                "password": "NewUser123",
                "confirm": "NewUser123",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

        # User should be created
        user = User.query.filter_by(username="newuser").first()
        assert user is not None
        assert user.check_password("NewUser123")

        # User should be logged in
        with client.session_transaction() as sess:
            assert sess.get("user_id") == user.id

    def test_register_with_existing_username(self, client, user):
        """Test registration with existing username."""
        response = client.post(
            "/register",
            data={
                "username": "testuser",
                "password": "NewUser123",
                "confirm": "NewUser123",
            },
        )
        assert response.status_code == 400
        assert b"already exists" in response.data

    def test_register_with_password_mismatch(self, client):
        """Test registration with mismatched passwords."""
        response = client.post(
            "/register",
            data={
                "username": "newuser",
                "password": "Password123",
                "confirm": "DifferentPassword123",
            },
        )
        assert response.status_code == 400
        assert b"do not match" in response.data

    def test_register_with_short_password(self, client):
        """Test registration with password that's too short."""
        response = client.post(
            "/register",
            data={
                "username": "newuser",
                "password": "Short1",
                "confirm": "Short1",
            },
        )
        assert response.status_code == 400
        assert b"8 characters" in response.data

    def test_register_with_no_digit_in_password(self, client):
        """Test registration with password without digit."""
        response = client.post(
            "/register",
            data={
                "username": "newuser",
                "password": "PasswordNoDigit",
                "confirm": "PasswordNoDigit",
            },
        )
        assert response.status_code == 400
        assert b"number" in response.data.lower()

    def test_register_with_invalid_username(self, client):
        """Test registration with invalid username."""
        response = client.post(
            "/register",
            data={
                "username": "ab",  # Too short
                "password": "Password123",
                "confirm": "Password123",
            },
        )
        assert response.status_code == 400

    def test_register_redirects_if_already_logged_in(self, authenticated_client):
        """Test that logged-in users are redirected from register page."""
        response = authenticated_client.get("/register", follow_redirects=False)
        assert response.status_code == 302
        assert response.location == "/"


class TestLogout:
    """Tests for logout functionality."""

    def test_successful_logout(self, authenticated_client, user):
        """Test successful logout."""
        # Verify user is logged in
        with authenticated_client.session_transaction() as sess:
            assert sess.get("user_id") == user.id

        # Logout
        response = authenticated_client.post("/logout", follow_redirects=True)
        assert response.status_code == 200

        # Session should be cleared
        with authenticated_client.session_transaction() as sess:
            assert sess.get("user_id") is None

    def test_logout_requires_login(self, client):
        """Test that logout requires authentication."""
        response = client.post("/logout", follow_redirects=False)
        assert response.status_code == 302
        assert response.location == "/login"


class TestLoginRequired:
    """Tests for login_required decorator."""

    def test_index_requires_login(self, client):
        """Test that index page requires login."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert response.location == "/login"

    def test_api_todos_requires_login(self, client):
        """Test that API endpoints require login."""
        response = client.get("/api/todos")
        assert response.status_code == 401
        assert b"Authentication required" in response.data

    def test_authenticated_user_can_access_protected_routes(
        self, authenticated_client
    ):
        """Test that authenticated users can access protected routes."""
        response = authenticated_client.get("/")
        assert response.status_code == 200

        response = authenticated_client.get("/api/todos")
        assert response.status_code == 200
