"""Unit tests for AI summary generation."""

import pytest
import json
from datetime import datetime, timedelta

from app import generate_ai_summary
from models import Todo


@pytest.mark.unit
class TestAISummaryGeneration:
    """Tests for AI summary generation logic."""

    def test_ai_summary_basic_structure(self, todo, user):
        """Test that AI summary has correct structure."""
        summary = generate_ai_summary(todo, user)

        assert 'summary' in summary
        assert 'suggestions' in summary
        assert 'insights' in summary
        assert 'stats' in summary

        assert isinstance(summary['summary'], str)
        assert isinstance(summary['suggestions'], list)
        assert isinstance(summary['insights'], list)
        assert isinstance(summary['stats'], dict)

    def test_ai_summary_stats(self, todo, user):
        """Test that stats contain correct information."""
        summary = generate_ai_summary(todo, user)
        stats = summary['stats']

        assert 'days_since_created' in stats
        assert 'hours_since_updated' in stats
        assert 'progress_percentage' in stats
        assert 'is_completed' in stats

        assert stats['progress_percentage'] == todo.progress
        assert stats['is_completed'] == todo.completed

    def test_ai_summary_new_task(self, db, user):
        """Test AI summary for newly created task."""
        todo = Todo(user_id=user.id, text='New task', progress=0, completed=False)
        db.session.add(todo)
        db.session.commit()

        summary = generate_ai_summary(todo, user)

        assert 'ready to begin' in summary['summary'].lower()
        assert summary['stats']['days_since_created'] == 0

    def test_ai_summary_completed_task(self, completed_todo, user):
        """Test AI summary for completed task."""
        summary = generate_ai_summary(completed_todo, user)

        assert 'completed' in summary['summary'].lower()
        assert summary['stats']['is_completed'] is True

    def test_ai_summary_high_progress(self, db, user):
        """Test AI summary for task with high progress."""
        todo = Todo(user_id=user.id, text='Almost done', progress=85, completed=False)
        db.session.add(todo)
        db.session.commit()

        summary = generate_ai_summary(todo, user)

        assert 'almost' in summary['summary'].lower() or '85%' in summary['summary']

    def test_ai_summary_medium_progress(self, db, user):
        """Test AI summary for task with medium progress."""
        todo = Todo(user_id=user.id, text='Halfway', progress=50, completed=False)
        db.session.add(todo)
        db.session.commit()

        summary = generate_ai_summary(todo, user)

        assert 'halfway' in summary['summary'].lower() or '50%' in summary['summary']

    def test_ai_summary_low_progress(self, db, user):
        """Test AI summary for task with low progress."""
        todo = Todo(user_id=user.id, text='Just started', progress=10, completed=False)
        db.session.add(todo)
        db.session.commit()

        summary = generate_ai_summary(todo, user)

        assert '10%' in summary['summary'] or 'started' in summary['summary'].lower()

    def test_ai_suggestions_urgent_task(self, urgent_todo, user):
        """Test AI suggestions for urgent task."""
        summary = generate_ai_summary(urgent_todo, user)

        # Should have priority suggestion
        suggestions = summary['suggestions']
        assert len(suggestions) > 0

        priority_suggestion = next((s for s in suggestions if s['type'] == 'priority'), None)
        assert priority_suggestion is not None
        assert 'priority' in priority_suggestion['text'].lower()

    def test_ai_suggestions_meeting_task(self, meeting_todo, user):
        """Test AI suggestions for meeting task."""
        summary = generate_ai_summary(meeting_todo, user)

        suggestions = summary['suggestions']
        meeting_suggestion = next((s for s in suggestions if s['type'] == 'meeting'), None)
        assert meeting_suggestion is not None
        assert 'meeting' in meeting_suggestion['text'].lower() or 'calendar' in meeting_suggestion['text'].lower()

    def test_ai_suggestions_email_task(self, db, user):
        """Test AI suggestions for email task."""
        todo = Todo(
            user_id=user.id,
            text='Send email to team',
            notes='Need to reply to the message',
            progress=0,
            completed=False
        )
        db.session.add(todo)
        db.session.commit()

        summary = generate_ai_summary(todo, user)

        suggestions = summary['suggestions']
        email_suggestion = next((s for s in suggestions if s['type'] == 'email'), None)
        assert email_suggestion is not None

    def test_ai_suggestions_learning_task(self, db, user):
        """Test AI suggestions for learning task."""
        todo = Todo(
            user_id=user.id,
            text='Learn Python programming',
            notes='Study advanced topics',
            progress=20,
            completed=False
        )
        db.session.add(todo)
        db.session.commit()

        summary = generate_ai_summary(todo, user)

        suggestions = summary['suggestions']
        learning_suggestion = next((s for s in suggestions if s['type'] == 'learning'), None)
        assert learning_suggestion is not None

    def test_ai_suggestions_shopping_task(self, db, user):
        """Test AI suggestions for shopping task."""
        todo = Todo(
            user_id=user.id,
            text='Buy groceries for dinner',
            progress=0,
            completed=False
        )
        db.session.add(todo)
        db.session.commit()

        summary = generate_ai_summary(todo, user)

        suggestions = summary['suggestions']
        shopping_suggestion = next((s for s in suggestions if s['type'] == 'shopping'), None)
        assert shopping_suggestion is not None

    def test_ai_suggestions_planning_task(self, db, user):
        """Test AI suggestions for planning task."""
        todo = Todo(
            user_id=user.id,
            text='Plan project timeline and schedule',
            progress=0,
            completed=False
        )
        db.session.add(todo)
        db.session.commit()

        summary = generate_ai_summary(todo, user)

        suggestions = summary['suggestions']
        planning_suggestion = next((s for s in suggestions if s['type'] == 'planning'), None)
        assert planning_suggestion is not None

    def test_ai_suggestions_writing_task(self, db, user):
        """Test AI suggestions for writing task."""
        todo = Todo(
            user_id=user.id,
            text='Write blog article',
            notes='Document the new feature',
            progress=0,
            completed=False
        )
        db.session.add(todo)
        db.session.commit()

        summary = generate_ai_summary(todo, user)

        suggestions = summary['suggestions']
        writing_suggestion = next((s for s in suggestions if s['type'] == 'writing'), None)
        assert writing_suggestion is not None

    def test_ai_suggestions_review_task(self, db, user):
        """Test AI suggestions for review task."""
        todo = Todo(
            user_id=user.id,
            text='Review code and test changes',
            progress=0,
            completed=False
        )
        db.session.add(todo)
        db.session.commit()

        summary = generate_ai_summary(todo, user)

        suggestions = summary['suggestions']
        review_suggestion = next((s for s in suggestions if s['type'] == 'review'), None)
        assert review_suggestion is not None

    def test_ai_suggestions_old_task(self, old_todo, user):
        """Test AI suggestions for old pending task."""
        summary = generate_ai_summary(old_todo, user)

        suggestions = summary['suggestions']
        # Should suggest breaking down or reviewing the task
        assert len(suggestions) > 0

    def test_ai_suggestions_near_completion(self, db, user):
        """Test AI suggestions for task near completion."""
        todo = Todo(
            user_id=user.id,
            text='Final review',
            progress=90,
            completed=False
        )
        db.session.add(todo)
        db.session.commit()

        summary = generate_ai_summary(todo, user)

        suggestions = summary['suggestions']
        completion_suggestion = next((s for s in suggestions if s['type'] == 'completion'), None)
        assert completion_suggestion is not None

    def test_ai_suggestions_limit(self, db, user):
        """Test that suggestions are limited to top 4."""
        # Create task with multiple keywords to trigger many suggestions
        todo = Todo(
            user_id=user.id,
            text='Urgent: Schedule important meeting, send email, and write report',
            notes='Need to research, plan, and review everything',
            progress=10,
            completed=False
        )
        db.session.add(todo)
        db.session.commit()

        summary = generate_ai_summary(todo, user)

        suggestions = summary['suggestions']
        assert len(suggestions) <= 4

    def test_ai_suggestions_default(self, db, user):
        """Test default suggestions when no keywords match."""
        todo = Todo(
            user_id=user.id,
            text='Random task xyz',
            progress=0,
            completed=False
        )
        db.session.add(todo)
        db.session.commit()

        summary = generate_ai_summary(todo, user)

        suggestions = summary['suggestions']
        assert len(suggestions) > 0
        # Should have general suggestions
        general_suggestion = next((s for s in suggestions if s['type'] == 'general'), None)
        assert general_suggestion is not None

    def test_ai_insights_progress_velocity(self, db, user):
        """Test AI insights for task with progress."""
        todo = Todo(
            user_id=user.id,
            text='Task with progress',
            progress=50,
            completed=False
        )
        db.session.add(todo)
        db.session.commit()

        summary = generate_ai_summary(todo, user)

        # Insights may or may not be present depending on timing
        assert 'insights' in summary
        assert isinstance(summary['insights'], list)

    def test_ai_summary_timestamp_formatting(self, db, user):
        """Test that timestamps are correctly formatted in summary."""
        todo = Todo(user_id=user.id, text='Task', progress=0, completed=False)
        db.session.add(todo)
        db.session.commit()

        summary = generate_ai_summary(todo, user)

        # Should mention "today" for new tasks
        assert 'today' in summary['summary'].lower() or 'created today' in summary['summary'].lower()

    def test_ai_summary_old_task_formatting(self, old_todo, user):
        """Test AI summary for old task mentions timeframe."""
        summary = generate_ai_summary(old_todo, user)

        # Should mention days/weeks/months
        assert any(word in summary['summary'].lower() for word in ['day', 'week', 'month', 'ago'])


@pytest.mark.unit
class TestAISummaryAPIEndpoint:
    """Tests for AI summary API endpoint."""

    def test_ai_summary_endpoint_requires_auth(self, client, todo):
        """Test that AI summary endpoint requires authentication."""
        response = client.get(f'/api/todos/{todo.id}/ai-summary')
        assert response.status_code == 302

    def test_ai_summary_endpoint_success(self, authenticated_client, todo):
        """Test successful AI summary retrieval."""
        response = authenticated_client.get(f'/api/todos/{todo.id}/ai-summary')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'summary' in data
        assert 'suggestions' in data
        assert 'insights' in data
        assert 'stats' in data

    def test_ai_summary_endpoint_not_found(self, authenticated_client):
        """Test AI summary for non-existent todo."""
        response = authenticated_client.get('/api/todos/99999/ai-summary')
        assert response.status_code == 404

    def test_ai_summary_endpoint_wrong_user(self, authenticated_client, another_user, db):
        """Test that users can't access other users' todo summaries."""
        todo = Todo(user_id=another_user.id, text='Other user task', completed=False)
        db.session.add(todo)
        db.session.commit()

        response = authenticated_client.get(f'/api/todos/{todo.id}/ai-summary')
        assert response.status_code == 404

    def test_ai_summary_endpoint_completed_task(self, authenticated_client, completed_todo):
        """Test AI summary endpoint for completed task."""
        response = authenticated_client.get(f'/api/todos/{completed_todo.id}/ai-summary')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['stats']['is_completed'] is True
        assert 'completed' in data['summary'].lower()

    def test_ai_summary_endpoint_with_notes(self, authenticated_client, todo):
        """Test AI summary considers notes content."""
        response = authenticated_client.get(f'/api/todos/{todo.id}/ai-summary')

        assert response.status_code == 200
        data = json.loads(response.data)

        # Should analyze both text and notes
        assert len(data['suggestions']) > 0
