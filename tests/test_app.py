import sys
import os

# Add project root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the Flask app and database models
from app import app, db
from models import User, Transaction, Budget


# Create a test client for the Flask application
def test_home_page():
    tester = app.test_client()
    response = tester.get("/")

    # Check that home page loads successfully
    assert response.status_code == 200


# Test register page loads correctly
def test_register_page():
    tester = app.test_client()
    response = tester.get("/register")

    assert response.status_code == 200


# Test login page loads correctly
def test_login_page():
    tester = app.test_client()
    response = tester.get("/login")

    assert response.status_code == 200


# Test dashboard redirects if user is not logged in
def test_dashboard_requires_login():
    tester = app.test_client()
    response = tester.get("/dashboard")

    # Flask-Login redirects unauthenticated users to login page
    assert response.status_code == 302


# Test add transaction page redirects if user is not logged in
def test_add_transaction_requires_login():
    tester = app.test_client()
    response = tester.get("/add_transaction")

    assert response.status_code == 302


# Test budgets page redirects if user is not logged in
def test_budgets_requires_login():
    tester = app.test_client()
    response = tester.get("/budgets")

    assert response.status_code == 302


# Test logout redirects correctly
def test_logout_requires_login():
    tester = app.test_client()
    response = tester.get("/logout")

    assert response.status_code == 302
