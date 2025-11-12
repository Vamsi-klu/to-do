"""Unit tests for AI summary endpoint."""
import pytest
from unittest.mock import Mock, patch
import json


@pytest.mark.unit
@pytest.mark.ai
class TestAISummaryEndpoint:
    """Test AI summary endpoint."""

    def test_ai_summary_requires_login(self, client):
        """Test that AI summary endpoint requires authentication."""
        response = client.post('/api/ai/summary')
        assert response.status_code == 302  # Redirect to login

    def test_ai_summary_with_no_todos(self, authenticated_client, db):
        """Test AI summary when user has no todos."""
        response = authenticated_client.post('/api/ai/summary')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'summary' in data
        assert "don't have any tasks" in data['summary']

    @patch('app.OpenAI')
    def test_ai_summary_with_todos_success(self, mock_openai, authenticated_client, test_todos, mock_openai_response):
        """Test successful AI summary generation with todos."""
        # Mock OpenAI response
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response(
            "Great progress! You have 5 tasks total with 2 completed. Focus on finishing your project report next."
        )

        response = authenticated_client.post('/api/ai/summary')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'summary' in data
        assert len(data['summary']) > 0
        assert 'progress' in data['summary'].lower() or 'tasks' in data['summary'].lower()

        # Verify OpenAI was called correctly
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs['model'] == 'gpt-3.5-turbo'
        assert call_args.kwargs['max_tokens'] == 200
        assert len(call_args.kwargs['messages']) == 2

    @patch('app.OpenAI')
    def test_ai_summary_includes_task_counts(self, mock_openai, authenticated_client, test_todos, mock_openai_response):
        """Test that AI summary includes correct task counts."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response("Summary text")

        response = authenticated_client.post('/api/ai/summary')

        # Check that the prompt sent to OpenAI includes task information
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        user_message = messages[1]['content']

        # Should mention total tasks (5)
        assert '5' in user_message or 'five' in user_message.lower()
        # Should mention completed (2) and active (3) tasks
        assert '2' in user_message or 'two' in user_message.lower()
        assert '3' in user_message or 'three' in user_message.lower()

    def test_ai_summary_without_api_key(self, authenticated_client, test_todos, monkeypatch):
        """Test AI summary fails gracefully without API key."""
        # Remove API key
        monkeypatch.delenv('OPENAI_API_KEY', raising=False)
        monkeypatch.setenv('OPENAI_API_KEY', '')

        response = authenticated_client.post('/api/ai/summary')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not configured' in data['error'].lower()

    @patch('app.OpenAI')
    def test_ai_summary_openai_api_error(self, mock_openai, authenticated_client, test_todos):
        """Test AI summary handles OpenAI API errors."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        response = authenticated_client.post('/api/ai/summary')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Failed to generate summary' in data['error']

    @patch('app.OpenAI')
    def test_ai_summary_limits_tasks_in_prompt(self, mock_openai, authenticated_client, test_user, db, mock_openai_response):
        """Test that AI summary limits the number of tasks sent to OpenAI."""
        # Create 20 todos (more than the 10 active + 5 completed limit)
        from models import Todo
        for i in range(20):
            todo = Todo(user_id=test_user.id, text=f'Task {i}', completed=i < 10)
            db.session.add(todo)
        db.session.commit()

        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response("Summary")

        response = authenticated_client.post('/api/ai/summary')

        assert response.status_code == 200

        # Check that the prompt is limited
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        user_message = messages[1]['content']

        # Should mention "and X more" for tasks beyond the limit
        assert 'more' in user_message.lower()

    @patch('app.OpenAI')
    def test_ai_summary_response_format(self, mock_openai, authenticated_client, test_todos, mock_openai_response):
        """Test AI summary response format is correct."""
        expected_summary = "You're doing great! Keep it up."

        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response(expected_summary)

        response = authenticated_client.post('/api/ai/summary')

        assert response.status_code == 200
        assert response.content_type == 'application/json'

        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert 'summary' in data
        assert data['summary'] == expected_summary

    @patch('app.OpenAI')
    def test_ai_summary_system_prompt(self, mock_openai, authenticated_client, test_todos, mock_openai_response):
        """Test that AI summary uses appropriate system prompt."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response("Summary")

        response = authenticated_client.post('/api/ai/summary')

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        system_message = messages[0]

        assert system_message['role'] == 'system'
        assert 'summarize' in system_message['content'].lower()
        assert 'task' in system_message['content'].lower()

    @patch('app.OpenAI')
    def test_ai_summary_temperature_setting(self, mock_openai, authenticated_client, test_todos, mock_openai_response):
        """Test that AI summary uses appropriate temperature."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response("Summary")

        response = authenticated_client.post('/api/ai/summary')

        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs['temperature'] == 0.7
