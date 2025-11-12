"""Unit tests for Flask application routes and API endpoints."""

import pytest
import json
from datetime import datetime

from models import User, Todo
from database import db


@pytest.mark.unit
class TestAuthenticationRoutes:
    """Tests for authentication routes."""

    def test_login_page_get(self, client):
        """Test GET request to login page."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Welcome back' in response.data

    def test_login_successful(self, client, user):
        """Test successful login."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should redirect to index
        assert b'Your Tasks' in response.data

    def test_login_invalid_username(self, client, user):
        """Test login with invalid username."""
        response = client.post('/login', data={
            'username': 'wronguser',
            'password': 'testpassword'
        })

        assert response.status_code == 401
        assert b'Invalid credentials' in response.data

    def test_login_invalid_password(self, client, user):
        """Test login with invalid password."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        })

        assert response.status_code == 401
        assert b'Invalid credentials' in response.data

    def test_login_empty_credentials(self, client):
        """Test login with empty credentials."""
        response = client.post('/login', data={
            'username': '',
            'password': ''
        })

        assert response.status_code == 401

    def test_login_redirect_when_authenticated(self, authenticated_client):
        """Test that authenticated users are redirected from login page."""
        response = authenticated_client.get('/login', follow_redirects=True)
        assert response.status_code == 200
        assert b'Your Tasks' in response.data

    def test_register_page_get(self, client):
        """Test GET request to register page."""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Create' in response.data or b'Register' in response.data

    def test_register_successful(self, client, db):
        """Test successful registration."""
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'newpassword123',
            'confirm': 'newpassword123'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should be logged in and redirected
        assert b'Your Tasks' in response.data

        # Verify user was created
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.username == 'newuser'

    def test_register_password_mismatch(self, client):
        """Test registration with password mismatch."""
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'password123',
            'confirm': 'different123'
        })

        assert response.status_code == 400
        assert b'do not match' in response.data

    def test_register_existing_username(self, client, user):
        """Test registration with existing username."""
        response = client.post('/register', data={
            'username': 'testuser',
            'password': 'password123',
            'confirm': 'password123'
        })

        assert response.status_code == 400
        assert b'already exists' in response.data

    def test_register_empty_fields(self, client):
        """Test registration with empty fields."""
        response = client.post('/register', data={
            'username': '',
            'password': '',
            'confirm': ''
        })

        assert response.status_code == 400
        assert b'required' in response.data

    def test_logout(self, authenticated_client):
        """Test logout functionality."""
        response = authenticated_client.post('/logout', follow_redirects=True)

        assert response.status_code == 200
        assert b'Welcome back' in response.data  # Should redirect to login


@pytest.mark.unit
class TestIndexRoute:
    """Tests for index/home route."""

    def test_index_requires_authentication(self, client):
        """Test that index requires authentication."""
        response = client.get('/', follow_redirects=True)
        assert response.status_code == 200
        assert b'Welcome back' in response.data  # Redirected to login

    def test_index_authenticated(self, authenticated_client, user):
        """Test index page when authenticated."""
        response = authenticated_client.get('/')
        assert response.status_code == 200
        assert b'Your Tasks' in response.data
        assert b'testuser' in response.data


@pytest.mark.unit
class TestTodoAPIEndpoints:
    """Tests for Todo API endpoints."""

    def test_list_todos_requires_auth(self, client):
        """Test that listing todos requires authentication."""
        response = client.get('/api/todos')
        assert response.status_code == 302  # Redirect to login

    def test_list_todos_empty(self, authenticated_client):
        """Test listing todos when none exist."""
        response = authenticated_client.get('/api/todos')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_todos_with_data(self, authenticated_client, multiple_todos):
        """Test listing todos with existing data."""
        response = authenticated_client.get('/api/todos')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 5

    def test_list_todos_user_isolation(self, authenticated_client, user, another_user, db):
        """Test that users only see their own todos."""
        # Create todos for both users
        todo1 = Todo(user_id=user.id, text='User 1 todo', completed=False)
        todo2 = Todo(user_id=another_user.id, text='User 2 todo', completed=False)
        db.session.add(todo1)
        db.session.add(todo2)
        db.session.commit()

        response = authenticated_client.get('/api/todos')
        data = json.loads(response.data)

        assert len(data) == 1
        assert data[0]['text'] == 'User 1 todo'

    def test_create_todo_requires_auth(self, client):
        """Test that creating todo requires authentication."""
        response = client.post('/api/todos', json={'text': 'New task'})
        assert response.status_code == 302

    def test_create_todo_success(self, authenticated_client, db):
        """Test successfully creating a todo."""
        response = authenticated_client.post('/api/todos', json={
            'text': 'New task',
            'notes': 'Some notes',
            'progress': 25
        })

        assert response.status_code == 201
        data = json.loads(response.data)

        assert data['text'] == 'New task'
        assert data['notes'] == 'Some notes'
        assert data['progress'] == 25
        assert data['completed'] is False
        assert 'id' in data
        assert 'created_at' in data

    def test_create_todo_minimal(self, authenticated_client):
        """Test creating todo with minimal data."""
        response = authenticated_client.post('/api/todos', json={
            'text': 'Simple task'
        })

        assert response.status_code == 201
        data = json.loads(response.data)

        assert data['text'] == 'Simple task'
        assert data['progress'] == 0
        assert data['completed'] is False

    def test_create_todo_empty_text(self, authenticated_client):
        """Test creating todo with empty text."""
        response = authenticated_client.post('/api/todos', json={
            'text': ''
        })

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_todo_no_text(self, authenticated_client):
        """Test creating todo without text field."""
        response = authenticated_client.post('/api/todos', json={})

        assert response.status_code == 400

    def test_update_todo_requires_auth(self, client, todo):
        """Test that updating todo requires authentication."""
        response = client.patch(f'/api/todos/{todo.id}', json={'text': 'Updated'})
        assert response.status_code == 302

    def test_update_todo_text(self, authenticated_client, todo):
        """Test updating todo text."""
        response = authenticated_client.patch(f'/api/todos/{todo.id}', json={
            'text': 'Updated task'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['text'] == 'Updated task'

    def test_update_todo_notes(self, authenticated_client, todo):
        """Test updating todo notes."""
        response = authenticated_client.patch(f'/api/todos/{todo.id}', json={
            'notes': 'Updated notes'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['notes'] == 'Updated notes'

    def test_update_todo_progress(self, authenticated_client, todo):
        """Test updating todo progress."""
        response = authenticated_client.patch(f'/api/todos/{todo.id}', json={
            'progress': 75
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['progress'] == 75

    def test_update_todo_progress_clamping(self, authenticated_client, todo):
        """Test that progress is clamped to 0-100."""
        # Test above 100
        response = authenticated_client.patch(f'/api/todos/{todo.id}', json={
            'progress': 150
        })
        data = json.loads(response.data)
        assert data['progress'] == 100

        # Test below 0
        response = authenticated_client.patch(f'/api/todos/{todo.id}', json={
            'progress': -50
        })
        data = json.loads(response.data)
        assert data['progress'] == 0

    def test_update_todo_completed(self, authenticated_client, todo):
        """Test updating todo completion status."""
        response = authenticated_client.patch(f'/api/todos/{todo.id}', json={
            'completed': True
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['completed'] is True
        assert data['progress'] == 100  # Auto-set to 100

    def test_update_todo_completed_preserves_progress(self, authenticated_client, db, user):
        """Test that completing todo sets progress to 100."""
        todo = Todo(user_id=user.id, text='Task', progress=80, completed=False)
        db.session.add(todo)
        db.session.commit()

        response = authenticated_client.patch(f'/api/todos/{todo.id}', json={
            'completed': True
        })

        data = json.loads(response.data)
        assert data['progress'] == 100

    def test_update_todo_not_found(self, authenticated_client):
        """Test updating non-existent todo."""
        response = authenticated_client.patch('/api/todos/99999', json={
            'text': 'Updated'
        })

        assert response.status_code == 404

    def test_update_todo_wrong_user(self, authenticated_client, another_user, db):
        """Test that users can't update other users' todos."""
        todo = Todo(user_id=another_user.id, text='Other user task', completed=False)
        db.session.add(todo)
        db.session.commit()

        response = authenticated_client.patch(f'/api/todos/{todo.id}', json={
            'text': 'Hacked'
        })

        assert response.status_code == 404

    def test_update_todo_empty_text(self, authenticated_client, todo):
        """Test updating todo with empty text."""
        response = authenticated_client.patch(f'/api/todos/{todo.id}', json={
            'text': ''
        })

        assert response.status_code == 400

    def test_delete_todo_requires_auth(self, client, todo):
        """Test that deleting todo requires authentication."""
        response = client.delete(f'/api/todos/{todo.id}')
        assert response.status_code == 302

    def test_delete_todo_success(self, authenticated_client, todo, db):
        """Test successfully deleting a todo."""
        todo_id = todo.id

        response = authenticated_client.delete(f'/api/todos/{todo_id}')
        assert response.status_code == 204

        # Verify todo was deleted
        deleted_todo = db.session.get(Todo, todo_id)
        assert deleted_todo is None

    def test_delete_todo_not_found(self, authenticated_client):
        """Test deleting non-existent todo."""
        response = authenticated_client.delete('/api/todos/99999')
        assert response.status_code == 404

    def test_delete_todo_wrong_user(self, authenticated_client, another_user, db):
        """Test that users can't delete other users' todos."""
        todo = Todo(user_id=another_user.id, text='Other user task', completed=False)
        db.session.add(todo)
        db.session.commit()
        todo_id = todo.id

        response = authenticated_client.delete(f'/api/todos/{todo_id}')
        assert response.status_code == 404

        # Verify todo was not deleted
        still_exists = db.session.get(Todo, todo_id)
        assert still_exists is not None

    def test_serialize_todo(self, todo):
        """Test todo serialization."""
        from app import serialize_todo

        data = serialize_todo(todo)

        assert data['id'] == todo.id
        assert data['text'] == todo.text
        assert data['notes'] == todo.notes
        assert data['progress'] == todo.progress
        assert data['completed'] == todo.completed
        assert 'created_at' in data
        assert 'updated_at' in data
