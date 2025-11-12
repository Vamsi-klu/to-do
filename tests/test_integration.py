"""Integration tests for complete user flows."""

import pytest
import json
from models import User, Todo
from database import db


@pytest.mark.integration
class TestCompleteUserFlow:
    """Integration tests for complete user workflows."""

    def test_complete_registration_and_login_flow(self, client, db):
        """Test complete flow: register -> logout -> login."""
        # Register
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'securepass123',
            'confirm': 'securepass123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Your Tasks' in response.data

        # Verify user created
        user = User.query.filter_by(username='newuser').first()
        assert user is not None

        # Logout
        response = client.post('/logout', follow_redirects=True)
        assert b'Welcome back' in response.data

        # Login again
        response = client.post('/login', data={
            'username': 'newuser',
            'password': 'securepass123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Your Tasks' in response.data

    def test_complete_todo_crud_flow(self, authenticated_client, db):
        """Test complete CRUD flow for todos."""
        # Create todo
        response = authenticated_client.post('/api/todos', json={
            'text': 'Complete project',
            'notes': 'Important deadline',
            'progress': 0
        })
        assert response.status_code == 201
        created_data = json.loads(response.data)
        todo_id = created_data['id']

        # Read todos
        response = authenticated_client.get('/api/todos')
        assert response.status_code == 200
        todos = json.loads(response.data)
        assert len(todos) == 1
        assert todos[0]['text'] == 'Complete project'

        # Update todo - add progress
        response = authenticated_client.patch(f'/api/todos/{todo_id}', json={
            'progress': 50
        })
        assert response.status_code == 200
        updated_data = json.loads(response.data)
        assert updated_data['progress'] == 50

        # Update todo - add more notes
        response = authenticated_client.patch(f'/api/todos/{todo_id}', json={
            'notes': 'Important deadline - due Friday'
        })
        assert response.status_code == 200

        # Update todo - mark as complete
        response = authenticated_client.patch(f'/api/todos/{todo_id}', json={
            'completed': True
        })
        assert response.status_code == 200
        completed_data = json.loads(response.data)
        assert completed_data['completed'] is True
        assert completed_data['progress'] == 100

        # Delete todo
        response = authenticated_client.delete(f'/api/todos/{todo_id}')
        assert response.status_code == 204

        # Verify deletion
        response = authenticated_client.get('/api/todos')
        todos = json.loads(response.data)
        assert len(todos) == 0

    def test_multiple_todos_workflow(self, authenticated_client):
        """Test working with multiple todos."""
        # Create multiple todos
        todos = [
            {'text': 'Morning task', 'progress': 0},
            {'text': 'Afternoon task', 'progress': 50},
            {'text': 'Evening task', 'progress': 100, 'completed': True}
        ]

        created_ids = []
        for todo in todos:
            response = authenticated_client.post('/api/todos', json=todo)
            assert response.status_code == 201
            created_ids.append(json.loads(response.data)['id'])

        # List all todos
        response = authenticated_client.get('/api/todos')
        all_todos = json.loads(response.data)
        assert len(all_todos) == 3

        # Update each todo
        for i, todo_id in enumerate(created_ids):
            response = authenticated_client.patch(f'/api/todos/{todo_id}', json={
                'notes': f'Notes for task {i+1}'
            })
            assert response.status_code == 200

        # Delete first todo
        response = authenticated_client.delete(f'/api/todos/{created_ids[0]}')
        assert response.status_code == 204

        # Verify count
        response = authenticated_client.get('/api/todos')
        remaining_todos = json.loads(response.data)
        assert len(remaining_todos) == 2

    def test_progressive_task_completion_flow(self, authenticated_client):
        """Test progressive completion of a task."""
        # Create task
        response = authenticated_client.post('/api/todos', json={
            'text': 'Big project',
            'notes': 'Multi-step task',
            'progress': 0
        })
        todo_id = json.loads(response.data)['id']

        # Progress through stages
        stages = [25, 50, 75, 100]
        for progress in stages:
            response = authenticated_client.patch(f'/api/todos/{todo_id}', json={
                'progress': progress
            })
            data = json.loads(response.data)
            assert data['progress'] == progress

            # Get AI summary at each stage
            response = authenticated_client.get(f'/api/todos/{todo_id}/ai-summary')
            assert response.status_code == 200
            summary = json.loads(response.data)
            assert summary['stats']['progress_percentage'] == progress

        # Mark as complete
        response = authenticated_client.patch(f'/api/todos/{todo_id}', json={
            'completed': True
        })
        data = json.loads(response.data)
        assert data['completed'] is True

    def test_ai_summary_workflow(self, authenticated_client):
        """Test workflow involving AI summaries."""
        # Create task with specific keywords
        response = authenticated_client.post('/api/todos', json={
            'text': 'Urgent: Schedule team meeting',
            'notes': 'Need to send calendar invites and prepare agenda',
            'progress': 0
        })
        todo_id = json.loads(response.data)['id']

        # Get AI summary
        response = authenticated_client.get(f'/api/todos/{todo_id}/ai-summary')
        assert response.status_code == 200
        summary = json.loads(response.data)

        # Verify AI detected urgency and meeting
        assert 'summary' in summary
        suggestions = summary['suggestions']
        assert len(suggestions) > 0

        # Should have priority and meeting suggestions
        suggestion_types = [s['type'] for s in suggestions]
        assert 'priority' in suggestion_types or 'meeting' in suggestion_types

    def test_multi_user_isolation_flow(self, client, db):
        """Test that multiple users' data is isolated."""
        # Register first user
        client.post('/register', data={
            'username': 'user1',
            'password': 'pass1',
            'confirm': 'pass1'
        })

        # Create todo for user1
        response = client.post('/api/todos', json={
            'text': 'User1 task'
        })
        assert response.status_code == 201
        user1_todo_id = json.loads(response.data)['id']

        # Logout
        client.post('/logout')

        # Register second user
        client.post('/register', data={
            'username': 'user2',
            'password': 'pass2',
            'confirm': 'pass2'
        })

        # Create todo for user2
        response = client.post('/api/todos', json={
            'text': 'User2 task'
        })
        assert response.status_code == 201

        # User2 should only see their own todo
        response = client.get('/api/todos')
        todos = json.loads(response.data)
        assert len(todos) == 1
        assert todos[0]['text'] == 'User2 task'

        # User2 should not be able to access user1's todo
        response = client.get(f'/api/todos/{user1_todo_id}/ai-summary')
        assert response.status_code == 404

        response = client.patch(f'/api/todos/{user1_todo_id}', json={'text': 'Hacked'})
        assert response.status_code == 404

        response = client.delete(f'/api/todos/{user1_todo_id}')
        assert response.status_code == 404

    def test_task_lifecycle_with_notes(self, authenticated_client):
        """Test complete lifecycle of a task with detailed notes."""
        # Create task
        response = authenticated_client.post('/api/todos', json={
            'text': 'Research project',
            'notes': 'Initial research phase',
            'progress': 10
        })
        todo_id = json.loads(response.data)['id']

        # Update notes as work progresses
        notes_updates = [
            'Initial research phase - found 5 sources',
            'Analysis phase - created outline',
            'Writing phase - first draft complete',
            'Review phase - incorporated feedback',
            'Final version ready for submission'
        ]

        for i, notes in enumerate(notes_updates):
            progress = min(20 * (i + 1), 100)
            response = authenticated_client.patch(f'/api/todos/{todo_id}', json={
                'notes': notes,
                'progress': progress
            })
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['notes'] == notes
            assert data['progress'] == progress

        # Complete the task
        response = authenticated_client.patch(f'/api/todos/{todo_id}', json={
            'completed': True
        })
        data = json.loads(response.data)
        assert data['completed'] is True

    def test_error_handling_flow(self, authenticated_client):
        """Test error handling in typical workflows."""
        # Try to create todo without text
        response = authenticated_client.post('/api/todos', json={
            'notes': 'Notes without title'
        })
        assert response.status_code == 400

        # Create valid todo
        response = authenticated_client.post('/api/todos', json={
            'text': 'Valid task'
        })
        todo_id = json.loads(response.data)['id']

        # Try to update with empty text
        response = authenticated_client.patch(f'/api/todos/{todo_id}', json={
            'text': ''
        })
        assert response.status_code == 400

        # Try to access non-existent todo
        response = authenticated_client.get('/api/todos/99999/ai-summary')
        assert response.status_code == 404

        # Delete the valid todo
        response = authenticated_client.delete(f'/api/todos/{todo_id}')
        assert response.status_code == 204

        # Try to update deleted todo
        response = authenticated_client.patch(f'/api/todos/{todo_id}', json={
            'text': 'Updated'
        })
        assert response.status_code == 404


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database operations."""

    def test_database_transaction_rollback(self, app, db):
        """Test that failed transactions rollback properly."""
        with app.app_context():
            user = User(username='testuser')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

            try:
                # Try to create duplicate user (should fail)
                duplicate = User(username='testuser')
                duplicate.set_password('password')
                db.session.add(duplicate)
                db.session.commit()
            except:
                db.session.rollback()

            # Original user should still exist
            assert User.query.filter_by(username='testuser').count() == 1

    def test_cascade_delete_integration(self, app, db):
        """Test cascade delete behavior."""
        with app.app_context():
            user = User(username='testuser')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

            # Create multiple todos
            for i in range(5):
                todo = Todo(user_id=user.id, text=f'Task {i}', completed=False)
                db.session.add(todo)
            db.session.commit()

            assert Todo.query.filter_by(user_id=user.id).count() == 5

            # Delete user
            db.session.delete(user)
            db.session.commit()

            # All todos should be deleted
            assert Todo.query.filter_by(user_id=user.id).count() == 0

    def test_concurrent_updates(self, app, db):
        """Test handling of concurrent updates."""
        with app.app_context():
            user = User(username='testuser')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

            todo = Todo(user_id=user.id, text='Task', progress=0, completed=False)
            db.session.add(todo)
            db.session.commit()

            # Simulate concurrent updates
            todo.progress = 50
            todo.notes = 'Updated notes'
            db.session.commit()

            # Verify both updates persisted
            refreshed = db.session.get(Todo, todo.id)
            assert refreshed.progress == 50
            assert refreshed.notes == 'Updated notes'


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Integration tests for performance scenarios."""

    def test_many_todos_performance(self, authenticated_client, db, user):
        """Test handling many todos."""
        # Create 100 todos
        for i in range(100):
            todo = Todo(
                user_id=user.id,
                text=f'Task {i}',
                notes=f'Notes for task {i}',
                progress=i % 101,
                completed=(i % 10 == 0)
            )
            db.session.add(todo)
        db.session.commit()

        # List all todos
        response = authenticated_client.get('/api/todos')
        assert response.status_code == 200
        todos = json.loads(response.data)
        assert len(todos) == 100

    def test_bulk_operations(self, authenticated_client):
        """Test bulk create and delete operations."""
        # Bulk create
        created_ids = []
        for i in range(50):
            response = authenticated_client.post('/api/todos', json={
                'text': f'Bulk task {i}',
                'progress': 0
            })
            assert response.status_code == 201
            created_ids.append(json.loads(response.data)['id'])

        # Verify all created
        response = authenticated_client.get('/api/todos')
        todos = json.loads(response.data)
        assert len(todos) == 50

        # Bulk delete
        for todo_id in created_ids:
            response = authenticated_client.delete(f'/api/todos/{todo_id}')
            assert response.status_code == 204

        # Verify all deleted
        response = authenticated_client.get('/api/todos')
        todos = json.loads(response.data)
        assert len(todos) == 0
