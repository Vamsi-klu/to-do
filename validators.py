"""Input validation utilities."""
from __future__ import annotations

import re
from typing import Tuple


def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username format.

    Args:
        username: Username to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "Username is required"

    username = username.strip()

    if len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(username) > 80:
        return False, "Username must be less than 80 characters"

    # Allow alphanumeric, underscore, and hyphen
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"

    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password strength.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"

    if len(password) < 8:
        return False, "Password must be at least 8 characters"

    if len(password) > 128:
        return False, "Password must be less than 128 characters"

    # Check for at least one digit
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"

    # Check for at least one letter
    if not any(c.isalpha() for c in password):
        return False, "Password must contain at least one letter"

    return True, ""


def validate_todo_text(text: str) -> Tuple[bool, str]:
    """Validate todo text.

    Args:
        text: Todo text to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text:
        return False, "Task text is required"

    text = text.strip()

    if len(text) == 0:
        return False, "Task text cannot be empty or whitespace only"

    if len(text) > 500:
        return False, "Task text must be less than 500 characters"

    return True, ""


def validate_priority(priority: str) -> Tuple[bool, str]:
    """Validate priority value.

    Args:
        priority: Priority value to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_priorities = ["low", "medium", "high"]

    if priority not in valid_priorities:
        return False, f"Priority must be one of: {', '.join(valid_priorities)}"

    return True, ""


def validate_category(category: str) -> Tuple[bool, str]:
    """Validate category name.

    Args:
        category: Category name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not category:
        return True, ""  # Category is optional

    category = category.strip()

    if len(category) > 50:
        return False, "Category name must be less than 50 characters"

    return True, ""


def sanitize_string(text: str) -> str:
    """Sanitize string input by stripping whitespace.

    Args:
        text: String to sanitize

    Returns:
        Sanitized string
    """
    if not text:
        return ""
    return text.strip()
