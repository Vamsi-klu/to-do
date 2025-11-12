"""Unit tests for application routes."""
import pytest
import json


@pytest.mark.unit
class TestAuthRoutes:
    """Test authentication routes."""

    def test_login_page_get(self, client):
        """Test login page loads."""
        response = client.get('/login')
        assert response.status_code == 200

    def test_register_page_get(self, client):
        """Test register page loads."""
        response = client.get('/register')
        assert response.status_code == 200

    def test_login_redirects_if_already_logged_in(self, authenticated_client):
        """Test login redirects if user already logged in."""
        response = authenticated_client.get('/login')
        assert response.status_code == 302
        assert '/login' not in response.location

    def test_register_redirects_if_already_logged_in(self, authenticated_client):
        """Test register redirects if user already logged in."""
        response = authenticated_client.get('/register')
        assert response.status_code == 302

    def test_successful_registration(self, client, db):
        """Test successful user registration."""
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'newpass123',
            'confirm': 'newpass123'
        })
        assert response.status_code == 302  # Redirect after success

    def test_registration_password_mismatch(self, client):
        """Test registration fails with password mismatch."""
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'password1',
            'confirm': 'password2'
        })
        assert response.status_code == 400

    def test_registration_duplicate_username(self, client, test_user):
        """Test registration fails with duplicate username."""
        response = client.post('/register', data={
            'username': test_user.username,
            'password': 'newpass123',
            'confirm': 'newpass123'
        })
        assert response.status_code == 400

    def test_registration_empty_username(self, client):
        """Test registration fails with empty username."""
        response = client.post('/register', data={
            'username': '',
            'password': 'pass123',
            'confirm': 'pass123'
        })
        assert response.status_code == 400

    def test_registration_empty_password(self, client):
        """Test registration fails with empty password."""
        response = client.post('/register', data={
            'username': 'newuser',
            'password': '',
            'confirm': ''
        })
        assert response.status_code == 400

    def test_successful_login(self, client, test_user):
        """Test successful login."""
        response = client.post('/login', data={
            'username': test_user.username,
            'password': 'testpass123'
        })
        assert response.status_code == 302  # Redirect after success

    def test_login_wrong_password(self, client, test_user):
        """Test login fails with wrong password."""
        response = client.post('/login', data={
            'username': test_user.username,
            'password': 'wrongpassword'
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Test login fails with non-existent user."""
        response = client.post('/login', data={
            'username': 'nonexistent',
            'password': 'password'
        })
        assert response.status_code == 401

    def test_logout(self, authenticated_client):
        """Test logout."""
        response = authenticated_client.post('/logout')
        assert response.status_code == 302


@pytest.mark.unit
class TestTodoRoutes:
    """Test todo API routes."""

    def test_index_requires_login(self, client):
        """Test index page requires login."""
        response = client.get('/')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_index_with_login(self, authenticated_client):
        """Test index page with authenticated user."""
        response = authenticated_client.get('/')
        assert response.status_code == 200

    def test_list_todos_requires_login(self, client):
        """Test listing todos requires login."""
        response = client.get('/api/todos')
        assert response.status_code == 302

    def test_list_todos_authenticated(self, authenticated_client):
        """Test listing todos when authenticated."""
        response = authenticated_client.get('/api/todos')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_create_todo_requires_login(self, client):
        """Test creating todo requires login."""
        response = client.post('/api/todos',
            json={'text': 'Test'},
            content_type='application/json'
        )
        assert response.status_code == 302

    def test_create_todo_authenticated(self, authenticated_client):
        """Test creating todo when authenticated."""
        response = authenticated_client.post('/api/todos',
            json={'text': 'New task'},
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['text'] == 'New task'
        assert data['completed'] is False

    def test_create_todo_empty_text(self, authenticated_client):
        """Test creating todo with empty text fails."""
        response = authenticated_client.post('/api/todos',
            json={'text': '   '},
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_update_todo_requires_login(self, client, test_todos):
        """Test updating todo requires login."""
        response = client.patch(f'/api/todos/{test_todos[0].id}',
            json={'text': 'Updated'},
            content_type='application/json'
        )
        assert response.status_code == 302

    def test_update_todo_text(self, authenticated_client, test_todos):
        """Test updating todo text."""
        todo = test_todos[0]
        response = authenticated_client.patch(f'/api/todos/{todo.id}',
            json={'text': 'Updated text'},
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['text'] == 'Updated text'

    def test_update_todo_completed(self, authenticated_client, test_todos):
        """Test updating todo completion status."""
        todo = test_todos[0]
        response = authenticated_client.patch(f'/api/todos/{todo.id}',
            json={'completed': True},
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['completed'] is True

    def test_update_todo_empty_text_fails(self, authenticated_client, test_todos):
        """Test updating todo with empty text fails."""
        todo = test_todos[0]
        response = authenticated_client.patch(f'/api/todos/{todo.id}',
            json={'text': ''},
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_delete_todo_requires_login(self, client, test_todos):
        """Test deleting todo requires login."""
        response = client.delete(f'/api/todos/{test_todos[0].id}')
        assert response.status_code == 302

    def test_delete_todo_authenticated(self, authenticated_client, test_todos):
        """Test deleting todo when authenticated."""
        todo = test_todos[0]
        response = authenticated_client.delete(f'/api/todos/{todo.id}')
        assert response.status_code == 204

        # Verify deletion
        response = authenticated_client.get('/api/todos')
        todos = json.loads(response.data)
        assert not any(t['id'] == todo.id for t in todos)

    def test_delete_nonexistent_todo(self, authenticated_client):
        """Test deleting non-existent todo returns 404."""
        response = authenticated_client.delete('/api/todos/99999')
        assert response.status_code == 404

    def test_update_nonexistent_todo(self, authenticated_client):
        """Test updating non-existent todo returns 404."""
        response = authenticated_client.patch('/api/todos/99999',
            json={'text': 'Test'},
            content_type='application/json'
        )
        assert response.status_code == 404


@pytest.mark.unit
class TestSerializeTodo:
    """Test todo serialization."""

    def test_serialize_todo(self, test_todos):
        """Test todo serialization includes all fields."""
        from app import serialize_todo
        todo = test_todos[0]
        data = serialize_todo(todo)

        assert 'id' in data
        assert 'text' in data
        assert 'completed' in data
        assert 'created_at' in data
        assert 'updated_at' in data

        assert data['id'] == todo.id
        assert data['text'] == todo.text
        assert data['completed'] == todo.completed
