# Import the Flask app and database models
from app import app, db
from models import User, Transaction, Budget


# Create a test client for the Flask application
def test_home_page():
    tester = app.test_client()
    response = tester.get("/")

    # Check that home page loads successfully
    assert response.status_code == 200
