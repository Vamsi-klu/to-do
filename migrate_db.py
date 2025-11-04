"""
Database migration script to add new columns to existing Todo table.
Run this script to upgrade your existing database with the new features.
"""

from app import create_app
from database import db

def migrate():
    app = create_app()
    print("\n🔄 Starting database migration...\n")

    with app.app_context():
        # Check if columns already exist
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('todo')]

        print(f"Current columns in Todo table: {columns}\n")

        # Add missing columns
        migrations_needed = []

        if 'notes' not in columns:
            migrations_needed.append("ALTER TABLE todo ADD COLUMN notes TEXT")

        if 'progress' not in columns:
            migrations_needed.append("ALTER TABLE todo ADD COLUMN progress INTEGER DEFAULT 0 NOT NULL")

        if migrations_needed:
            print("📝 Applying migrations:")
            for migration in migrations_needed:
                print(f"  - {migration}")
                db.session.execute(db.text(migration))

            db.session.commit()
            print("\n✅ Database migration completed successfully!")
        else:
            print("✅ Database is already up to date. No migrations needed.")

        print("\n📊 Updated database schema:")
        inspector = db.inspect(db.engine)
        columns = inspector.get_columns('todo')
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")

if __name__ == "__main__":
    migrate()
