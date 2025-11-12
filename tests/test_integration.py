"""Integration tests for the application."""
import pytest
from unittest.mock import Mock, patch
import json
from models import Todo


@pytest.mark.integration
class TestAuthenticationFlow:
    """Test authentication integration."""

    def test_complete_auth_flow(self, client, db):
        """Test complete registration, login, logout flow."""
        # Register
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'newpass123',
            'confirm': 'newpass123'
        }, follow_redirects=True)
        assert response.status_code == 200

        # Logout
        response = client.post('/logout', follow_redirects=True)
        assert response.status_code == 200

        # Login
        response = client.post('/login', data={
            'username': 'newuser',
            'password': 'newpass123'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_invalid_login_redirects(self, client):
        """Test invalid login redirects properly."""
        response = client.post('/login', data={
            'username': 'wronguser',
            'password': 'wrongpass'
        })
        assert response.status_code == 401


@pytest.mark.integration
class TestTodoOperations:
    """Test todo CRUD operations integration."""

    def test_complete_todo_crud_flow(self, authenticated_client, db):
        """Test complete todo create, read, update, delete flow."""
        # Create
        response = authenticated_client.post('/api/todos',
            json={'text': 'Test Task'},
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        todo_id = data['id']

        # Read (list)
        response = authenticated_client.get('/api/todos')
        assert response.status_code == 200
        todos = json.loads(response.data)
        assert len(todos) == 1
        assert todos[0]['text'] == 'Test Task'

        # Update
        response = authenticated_client.patch(f'/api/todos/{todo_id}',
            json={'text': 'Updated Task', 'completed': True},
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['text'] == 'Updated Task'
        assert data['completed'] is True

        # Delete
        response = authenticated_client.delete(f'/api/todos/{todo_id}')
        assert response.status_code == 204

        # Verify deletion
        response = authenticated_client.get('/api/todos')
        todos = json.loads(response.data)
        assert len(todos) == 0


@pytest.mark.integration
@pytest.mark.ai
class TestAIWorkflow:
    """Test AI features integration workflow."""

    @patch('app.OpenAI')
    def test_ai_summary_after_adding_todos(self, mock_openai, authenticated_client, db, mock_openai_response):
        """Test getting AI summary after adding todos."""
        # Add some todos
        todos_to_add = ['Task 1', 'Task 2', 'Task 3']
        for text in todos_to_add:
            authenticated_client.post('/api/todos',
                json={'text': text},
                content_type='application/json'
            )

        # Mock OpenAI
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response("Good progress!")

        # Get AI summary
        response = authenticated_client.post('/api/ai/summary')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'summary' in data

    @patch('app.OpenAI')
    def test_ai_suggestions_workflow(self, mock_openai, authenticated_client, db, mock_openai_response):
        """Test getting suggestions, then adding suggested task."""
        # Add initial task
        authenticated_client.post('/api/todos',
            json={'text': 'Initial task'},
            content_type='application/json'
        )

        # Mock OpenAI for suggestions
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response(
            "Suggestions:\n1. Follow up on initial task\n2. Plan next steps"
        )

        # Get suggestions
        response = authenticated_client.post('/api/ai/suggestions')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'suggestions' in data

        # Add a suggested task
        response = authenticated_client.post('/api/todos',
            json={'text': 'Follow up on initial task'},
            content_type='application/json'
        )
        assert response.status_code == 201

        # Verify both tasks exist
        response = authenticated_client.get('/api/todos')
        todos = json.loads(response.data)
        assert len(todos) == 2

    @patch('app.OpenAI')
    def test_ai_features_with_completed_tasks(self, mock_openai, authenticated_client, test_user, db, mock_openai_response):
        """Test AI features workflow with mix of completed and active tasks."""
        # Add and complete some tasks
        for i in range(3):
            response = authenticated_client.post('/api/todos',
                json={'text': f'Task {i}'},
                content_type='application/json'
            )
            todo_id = json.loads(response.data)['id']

            # Complete first two tasks
            if i < 2:
                authenticated_client.patch(f'/api/todos/{todo_id}',
                    json={'completed': True},
                    content_type='application/json'
                )

        # Mock OpenAI
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response("Summary text")

        # Test summary includes both completed and active
        response = authenticated_client.post('/api/ai/summary')
        assert response.status_code == 200

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        user_message = messages[1]['content']

        # Should mention both completed and active tasks
        assert 'completed' in user_message.lower()
        assert 'active' in user_message.lower()


@pytest.mark.integration
class TestUserIsolation:
    """Test that users can only access their own data."""

    def test_users_cannot_access_other_todos(self, client, db):
        """Test that users can only see their own todos."""
        from models import User, Todo

        # Create two users
        user1 = User(username='user1')
        user1.set_password('pass1')
        user2 = User(username='user2')
        user2.set_password('pass2')
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        # Create todos for user1
        todo1 = Todo(user_id=user1.id, text='User 1 Task', completed=False)
        db.session.add(todo1)
        db.session.commit()

        # Login as user2
        with client.session_transaction() as sess:
            sess['user_id'] = user2.id

        # Try to access todos - should be empty for user2
        response = client.get('/api/todos')
        todos = json.loads(response.data)
        assert len(todos) == 0

        # Try to update user1's todo - should fail
        response = client.patch(f'/api/todos/{todo1.id}',
            json={'text': 'Hacked'},
            content_type='application/json'
        )
        assert response.status_code == 404

    @patch('app.OpenAI')
    def test_ai_summary_only_shows_user_todos(self, mock_openai, client, db, mock_openai_response):
        """Test that AI summary only includes current user's todos."""
        from models import User, Todo

        # Create two users with todos
        user1 = User(username='user1')
        user1.set_password('pass1')
        user2 = User(username='user2')
        user2.set_password('pass2')
        db.session.add_all([user1, user2])
        db.session.commit()

        # Add todos for both users
        todo1 = Todo(user_id=user1.id, text='User 1 Task', completed=False)
        todo2 = Todo(user_id=user2.id, text='User 2 Task', completed=False)
        db.session.add_all([todo1, todo2])
        db.session.commit()

        # Mock OpenAI
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response("Summary")

        # Login as user1
        with client.session_transaction() as sess:
            sess['user_id'] = user1.id

        # Get AI summary
        response = client.post('/api/ai/summary')
        assert response.status_code == 200

        # Check that only user1's tasks are in the prompt
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        user_message = messages[1]['content']

        assert 'User 1 Task' in user_message
        assert 'User 2 Task' not in user_message


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling across the application."""

    def test_404_for_nonexistent_todo(self, authenticated_client):
        """Test 404 response for non-existent todo."""
        response = authenticated_client.patch('/api/todos/99999',
            json={'text': 'Test'},
            content_type='application/json'
        )
        assert response.status_code == 404

    def test_invalid_json_payload(self, authenticated_client):
        """Test handling of invalid JSON payload."""
        response = authenticated_client.post('/api/todos',
            data='invalid json',
            content_type='application/json'
        )
        # Should handle gracefully (either 400 or process as empty)
        assert response.status_code in [400, 201]  # Depends on implementation

    def test_missing_required_field(self, authenticated_client):
        """Test handling of missing required fields."""
        response = authenticated_client.post('/api/todos',
            json={},
            content_type='application/json'
        )
        assert response.status_code == 400
