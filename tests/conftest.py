"""Test configuration and fixtures."""
import os
import pytest
from app import create_app
from database import db as _db
from models import User, Todo


@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    # Set test config
    os.environ['TESTING'] = 'True'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['OPENAI_API_KEY'] = 'test-key-123'

    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })

    # Create tables
    with app.app_context():
        _db.create_all()

    yield app

    # Cleanup
    with app.app_context():
        _db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    """Create database for the tests."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app, db):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(username='testuser')
    user.set_password('testpass123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def authenticated_client(client, test_user):
    """Create an authenticated test client."""
    with client.session_transaction() as sess:
        sess['user_id'] = test_user.id
    return client


@pytest.fixture
def test_todos(db, test_user):
    """Create test todos."""
    todos = [
        Todo(user_id=test_user.id, text='Buy groceries', completed=False),
        Todo(user_id=test_user.id, text='Finish project report', completed=False),
        Todo(user_id=test_user.id, text='Call dentist', completed=True),
        Todo(user_id=test_user.id, text='Exercise', completed=False),
        Todo(user_id=test_user.id, text='Read book', completed=True),
    ]
    for todo in todos:
        db.session.add(todo)
    db.session.commit()
    return todos


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    class MockMessage:
        def __init__(self, content):
            self.content = content

    class MockChoice:
        def __init__(self, message):
            self.message = message

    class MockCompletion:
        def __init__(self, content):
            self.choices = [MockChoice(MockMessage(content))]

    return MockCompletion
