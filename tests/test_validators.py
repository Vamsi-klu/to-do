"""Tests for input validators."""
from __future__ import annotations

import pytest
from validators import (
    validate_username,
    validate_password,
    validate_todo_text,
    validate_priority,
    validate_category,
    sanitize_string,
)


class TestValidateUsername:
    """Tests for username validation."""

    def test_valid_username(self):
        """Test valid usernames."""
        valid, error = validate_username("john_doe")
        assert valid is True
        assert error == ""

        valid, error = validate_username("user123")
        assert valid is True

        valid, error = validate_username("test-user")
        assert valid is True

        valid, error = validate_username("ABC")
        assert valid is True

    def test_empty_username(self):
        """Test empty username."""
        valid, error = validate_username("")
        assert valid is False
        assert "required" in error.lower()

    def test_username_too_short(self):
        """Test username that's too short."""
        valid, error = validate_username("ab")
        assert valid is False
        assert "3 characters" in error

    def test_username_too_long(self):
        """Test username that's too long."""
        valid, error = validate_username("a" * 81)
        assert valid is False
        assert "80 characters" in error

    def test_username_invalid_characters(self):
        """Test username with invalid characters."""
        valid, error = validate_username("user@name")
        assert valid is False
        assert "letters, numbers, underscores" in error.lower()

        valid, error = validate_username("user name")
        assert valid is False

        valid, error = validate_username("user!name")
        assert valid is False

    def test_username_with_whitespace(self):
        """Test username validation strips whitespace."""
        valid, error = validate_username("  testuser  ")
        assert valid is True  # Should strip and validate


class TestValidatePassword:
    """Tests for password validation."""

    def test_valid_password(self):
        """Test valid passwords."""
        valid, error = validate_password("Password123")
        assert valid is True
        assert error == ""

        valid, error = validate_password("MySecure1Pass")
        assert valid is True

    def test_empty_password(self):
        """Test empty password."""
        valid, error = validate_password("")
        assert valid is False
        assert "required" in error.lower()

    def test_password_too_short(self):
        """Test password that's too short."""
        valid, error = validate_password("Pass1")
        assert valid is False
        assert "8 characters" in error

    def test_password_too_long(self):
        """Test password that's too long."""
        valid, error = validate_password("a" * 129)
        assert valid is False
        assert "128 characters" in error

    def test_password_no_digit(self):
        """Test password without a digit."""
        valid, error = validate_password("PasswordNoDigit")
        assert valid is False
        assert "number" in error.lower()

    def test_password_no_letter(self):
        """Test password without a letter."""
        valid, error = validate_password("12345678")
        assert valid is False
        assert "letter" in error.lower()

    def test_password_with_special_characters(self):
        """Test password with special characters (should be valid)."""
        valid, error = validate_password("P@ssw0rd!")
        assert valid is True


class TestValidateTodoText:
    """Tests for todo text validation."""

    def test_valid_todo_text(self):
        """Test valid todo text."""
        valid, error = validate_todo_text("Buy groceries")
        assert valid is True
        assert error == ""

        valid, error = validate_todo_text("A")
        assert valid is True

    def test_empty_todo_text(self):
        """Test empty todo text."""
        valid, error = validate_todo_text("")
        assert valid is False
        assert "required" in error.lower()

    def test_whitespace_only_todo_text(self):
        """Test whitespace-only todo text."""
        valid, error = validate_todo_text("   ")
        assert valid is False
        assert "empty" in error.lower() or "whitespace" in error.lower()

    def test_todo_text_too_long(self):
        """Test todo text that's too long."""
        valid, error = validate_todo_text("a" * 501)
        assert valid is False
        assert "500 characters" in error

    def test_todo_text_exactly_500_chars(self):
        """Test todo text at maximum length."""
        valid, error = validate_todo_text("a" * 500)
        assert valid is True


class TestValidatePriority:
    """Tests for priority validation."""

    def test_valid_priorities(self):
        """Test valid priority values."""
        valid, error = validate_priority("low")
        assert valid is True
        assert error == ""

        valid, error = validate_priority("medium")
        assert valid is True

        valid, error = validate_priority("high")
        assert valid is True

    def test_invalid_priority(self):
        """Test invalid priority values."""
        valid, error = validate_priority("urgent")
        assert valid is False
        assert "low, medium, high" in error.lower()

        valid, error = validate_priority("critical")
        assert valid is False

        valid, error = validate_priority("")
        assert valid is False


class TestValidateCategory:
    """Tests for category validation."""

    def test_valid_category(self):
        """Test valid category names."""
        valid, error = validate_category("work")
        assert valid is True
        assert error == ""

        valid, error = validate_category("personal")
        assert valid is True

    def test_empty_category(self):
        """Test empty category (should be valid as optional)."""
        valid, error = validate_category("")
        assert valid is True

    def test_category_too_long(self):
        """Test category that's too long."""
        valid, error = validate_category("a" * 51)
        assert valid is False
        assert "50 characters" in error

    def test_category_exactly_50_chars(self):
        """Test category at maximum length."""
        valid, error = validate_category("a" * 50)
        assert valid is True


class TestSanitizeString:
    """Tests for string sanitization."""

    def test_sanitize_normal_string(self):
        """Test sanitizing normal string."""
        assert sanitize_string("hello") == "hello"

    def test_sanitize_string_with_whitespace(self):
        """Test sanitizing string with leading/trailing whitespace."""
        assert sanitize_string("  hello  ") == "hello"
        assert sanitize_string("\thello\n") == "hello"
        assert sanitize_string("  spaces  ") == "spaces"

    def test_sanitize_empty_string(self):
        """Test sanitizing empty string."""
        assert sanitize_string("") == ""

    def test_sanitize_none(self):
        """Test sanitizing None."""
        assert sanitize_string(None) == ""

    def test_sanitize_whitespace_only(self):
        """Test sanitizing whitespace-only string."""
        assert sanitize_string("   ") == ""
        assert sanitize_string("\t\n") == ""
