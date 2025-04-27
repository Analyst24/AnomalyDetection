import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix


class Base(DeclarativeBase):
    pass


# Initialize SQLAlchemy with the Base class
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "energy-detection-system-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database - supports both PostgreSQL and SQLite for offline use
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # Use PostgreSQL if DATABASE_URL is provided
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
else:
    # Fallback to SQLite for offline use
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(basedir, 'instance', 'energy_anomaly.db')}"
    # Make sure the instance directory exists
    os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["WTF_CSRF_ENABLED"] = True
app.config["WTF_CSRF_SECRET_KEY"] = os.environ.get("SESSION_SECRET", "energy-detection-system-csrf-key")

# Initialize SQLAlchemy with the app
db.init_app(app)

# Initialize CSRF protection
csrf = CSRFProtect()
csrf.init_app(app)

# CSRF exempt routes (for direct login/register)
csrf.exempt('routes.login')
csrf.exempt('routes.register')

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Create database tables within app context
with app.app_context():
    # Import models to register them with SQLAlchemy
    from models import User, Dataset, AnomalyResult
    db.create_all()

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))
    
# Import and initialize routes
from routes import init_routes
init_routes(app)
