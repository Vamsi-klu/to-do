"""Unit tests for AI suggestions endpoint."""
import pytest
from unittest.mock import Mock, patch
import json


@pytest.mark.unit
@pytest.mark.ai
class TestAISuggestionsEndpoint:
    """Test AI suggestions endpoint."""

    def test_ai_suggestions_requires_login(self, client):
        """Test that AI suggestions endpoint requires authentication."""
        response = client.post('/api/ai/suggestions')
        assert response.status_code == 302  # Redirect to login

    @patch('app.OpenAI')
    def test_ai_suggestions_with_no_todos(self, mock_openai, authenticated_client, db, mock_openai_response):
        """Test AI suggestions when user has no todos."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response(
            "Here are some task suggestions:\n1. Plan your week\n2. Set up a morning routine\n3. Organize your workspace"
        )

        response = authenticated_client.post('/api/ai/suggestions')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'suggestions' in data
        assert len(data['suggestions']) > 0

        # Verify the prompt mentions no tasks
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        user_message = messages[1]['content']
        assert 'no tasks' in user_message.lower()

    @patch('app.OpenAI')
    def test_ai_suggestions_with_todos_success(self, mock_openai, authenticated_client, test_todos, mock_openai_response):
        """Test successful AI suggestions generation with todos."""
        expected_suggestions = "Based on your tasks:\n1. Schedule grocery delivery\n2. Set project deadline\n3. Book dental checkup"

        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response(expected_suggestions)

        response = authenticated_client.post('/api/ai/suggestions')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'suggestions' in data
        assert data['suggestions'] == expected_suggestions

        # Verify OpenAI was called correctly
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs['model'] == 'gpt-3.5-turbo'
        assert call_args.kwargs['max_tokens'] == 250
        assert call_args.kwargs['temperature'] == 0.8
        assert len(call_args.kwargs['messages']) == 2

    @patch('app.OpenAI')
    def test_ai_suggestions_includes_existing_tasks(self, mock_openai, authenticated_client, test_todos, mock_openai_response):
        """Test that AI suggestions includes existing tasks in prompt."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response("Suggestions")

        response = authenticated_client.post('/api/ai/suggestions')

        # Check that the prompt includes existing tasks
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        user_message = messages[1]['content']

        # Should mention some of the test tasks
        assert 'groceries' in user_message.lower() or 'project' in user_message.lower()

    @patch('app.OpenAI')
    def test_ai_suggestions_shows_completion_status(self, mock_openai, authenticated_client, test_todos, mock_openai_response):
        """Test that suggestions prompt shows task completion status."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response("Suggestions")

        response = authenticated_client.post('/api/ai/suggestions')

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        user_message = messages[1]['content']

        # Should include completion markers (✓ or ○)
        assert '✓' in user_message or '○' in user_message

    def test_ai_suggestions_without_api_key(self, authenticated_client, test_todos, monkeypatch):
        """Test AI suggestions fails gracefully without API key."""
        # Remove API key
        monkeypatch.delenv('OPENAI_API_KEY', raising=False)
        monkeypatch.setenv('OPENAI_API_KEY', '')

        response = authenticated_client.post('/api/ai/suggestions')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not configured' in data['error'].lower()

    @patch('app.OpenAI')
    def test_ai_suggestions_openai_api_error(self, mock_openai, authenticated_client, test_todos):
        """Test AI suggestions handles OpenAI API errors."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        response = authenticated_client.post('/api/ai/suggestions')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Failed to generate suggestions' in data['error']

    @patch('app.OpenAI')
    def test_ai_suggestions_limits_tasks_in_prompt(self, mock_openai, authenticated_client, test_user, db, mock_openai_response):
        """Test that AI suggestions limits tasks sent to OpenAI."""
        # Create 20 todos (more than the 15 task limit)
        from models import Todo
        for i in range(20):
            todo = Todo(user_id=test_user.id, text=f'Task {i}', completed=False)
            db.session.add(todo)
        db.session.commit()

        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response("Suggestions")

        response = authenticated_client.post('/api/ai/suggestions')

        assert response.status_code == 200

        # Check that the prompt mentions additional tasks
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        user_message = messages[1]['content']

        # Should mention "and X more" for tasks beyond the limit
        assert 'more' in user_message.lower()

    @patch('app.OpenAI')
    def test_ai_suggestions_response_format(self, mock_openai, authenticated_client, test_todos, mock_openai_response):
        """Test AI suggestions response format is correct."""
        expected_suggestions = "1. Task A\n2. Task B\n3. Task C"

        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response(expected_suggestions)

        response = authenticated_client.post('/api/ai/suggestions')

        assert response.status_code == 200
        assert response.content_type == 'application/json'

        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert 'suggestions' in data
        assert data['suggestions'] == expected_suggestions

    @patch('app.OpenAI')
    def test_ai_suggestions_system_prompt(self, mock_openai, authenticated_client, test_todos, mock_openai_response):
        """Test that AI suggestions uses appropriate system prompt."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response("Suggestions")

        response = authenticated_client.post('/api/ai/suggestions')

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        system_message = messages[0]

        assert system_message['role'] == 'system'
        assert 'suggest' in system_message['content'].lower()
        assert 'task' in system_message['content'].lower()

    @patch('app.OpenAI')
    def test_ai_suggestions_temperature_higher_than_summary(self, mock_openai, authenticated_client, test_todos, mock_openai_response):
        """Test that suggestions uses higher temperature for creativity."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response("Suggestions")

        response = authenticated_client.post('/api/ai/suggestions')

        call_args = mock_client.chat.completions.create.call_args
        # Suggestions should use temperature 0.8 (higher than summary's 0.7)
        assert call_args.kwargs['temperature'] == 0.8

    @patch('app.OpenAI')
    def test_ai_suggestions_user_prompt_asks_for_suggestions(self, mock_openai, authenticated_client, test_todos, mock_openai_response):
        """Test that user prompt explicitly asks for task suggestions."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response("Suggestions")

        response = authenticated_client.post('/api/ai/suggestions')

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        user_message = messages[1]['content']

        assert 'suggest' in user_message.lower()
