from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


db = SQLAlchemy()
migrate = Migrate()


def init_db(app) -> None:
    """Bind SQLAlchemy and Flask-Migrate to app.

    Args:
        app: Flask application instance
    """
    db.init_app(app)
    migrate.init_app(app, db)

    # Create tables if they don't exist (for development/testing)
    # In production, use flask db upgrade
    with app.app_context():
        db.create_all()

