# 📋 To-Do App

A beautiful and simple to-do application built with Flask, SQLite, and Tailwind CSS. Features user authentication, CRUD operations for tasks, and a clean, responsive interface.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-v3.0.3-green.svg)
![SQLite](https://img.shields.io/badge/sqlite-v3-orange.svg)
![Tailwind](https://img.shields.io/badge/tailwind-v3-blue.svg)

## ✨ Features

- 🔐 **User Authentication**: Secure login and registration system
- ✅ **Task Management**: Create, read, update, and delete tasks
- 👤 **User-specific Tasks**: Each user has their own private task list
- 🎨 **Beautiful UI**: Modern design with Tailwind CSS
- 📱 **Responsive**: Works seamlessly on desktop and mobile
- 🔒 **Secure**: Passwords are hashed using Werkzeug security
- ⚡ **Fast**: Lightweight SQLite database with SQLAlchemy ORM

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Vamsi-klu/to-do.git
   cd to-do
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database and create a user**
   ```bash
   python bootstrap.py
   ```
   This will create the database tables and prompt you to create an initial user account.

5. **Run the application**
   ```bash
   flask --app app run --debug
   ```

6. **Open your browser**
   Navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000)

## 📁 Project Structure

```
to-do/
├── app.py              # Flask application and route definitions
├── database.py         # SQLAlchemy database initialization
├── models.py          # Database models (User, Todo)
├── bootstrap.py       # Database setup and user creation script
├── requirements.txt   # Python dependencies
├── templates/         # Jinja2 HTML templates
│   ├── base.html     # Base template with Tailwind CSS
│   ├── index.html    # Main todo list page
│   ├── login.html    # Login page
│   └── register.html # Registration page
├── static/           # Static assets
│   ├── js/
│   │   └── app.js   # Frontend JavaScript (Fetch API)
│   └── favicon.svg  # Application favicon
└── instance/        # Instance folder (contains database)
    └── db.sqlite3   # SQLite database file
```

## 🛠️ Technology Stack

- **Backend**: Flask 3.0.3 - Python web framework
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, Tailwind CSS (via CDN), Vanilla JavaScript
- **Authentication**: Session-based with hashed passwords
- **Development**: Flask development server with debug mode

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main todo list page (requires login) |
| GET | `/login` | Login page |
| POST | `/login` | Process login form |
| GET | `/register` | Registration page |
| POST | `/register` | Process registration form |
| POST | `/logout` | Logout user |
| POST | `/todos` | Create new todo |
| PUT | `/todos/<id>` | Update todo |
| DELETE | `/todos/<id>` | Delete todo |

## 🔧 Configuration

The application uses the following configuration options:

- `SECRET_KEY`: Session encryption key (auto-generated if not set)
- `DATABASE_URL`: Database connection string (defaults to SQLite)
- `SQLALCHEMY_TRACK_MODIFICATIONS`: Disabled for performance

You can set these as environment variables:

```bash
export SECRET_KEY="your-secret-key-here"
export DATABASE_URL="sqlite:///your-database.db"
```

## 🧪 Development

### Running in Development Mode

```bash
flask --app app run --debug
```

This enables:
- Hot reloading on file changes
- Detailed error pages
- Debug toolbar

### Database Operations

To reset the database:
```bash
rm instance/db.sqlite3  # Remove existing database
python bootstrap.py     # Recreate and initialize
```

## 📱 Usage

1. **Register**: Create a new account with username and password
2. **Login**: Sign in with your credentials
3. **Add Tasks**: Click "Add new todo" to create tasks
4. **Manage Tasks**: 
   - ✅ Mark tasks as complete/incomplete
   - ✏️ Edit task descriptions
   - 🗑️ Delete tasks you no longer need
5. **Logout**: Securely end your session

## 🔒 Security Features

- Passwords are hashed using Werkzeug's security utilities
- Session-based authentication
- User-specific data isolation
- CSRF protection through Flask sessions
- SQL injection prevention via SQLAlchemy ORM

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 👤 Author

**Ramachandra Nalam**
- GitHub: [@Vamsi-klu](https://github.com/Vamsi-klu)

## 🙏 Acknowledgments

- Flask team for the excellent web framework
- Tailwind CSS for beautiful, utility-first styling
- SQLAlchemy for powerful ORM capabilities

---

Made with ❤️ using Flask and Tailwind CSS
