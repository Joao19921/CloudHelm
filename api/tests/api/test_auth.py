from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import hash_password

def test_register_new_user(client: TestClient, db_session: Session):
    """Verify that a new user can successfully register via email and password."""
    payload = {
        "name": "QA Automation User",
        "email": "qa1@cloudhelm.com",
        "password": "StrongPassword123!"
    }
    
    response = client.post("/auth/register", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert "id" in data
    
    # Verify the database state directly
    user_in_db = db_session.query(User).filter(User.email == payload["email"]).first()
    assert user_in_db is not None
    assert user_in_db.name == payload["name"]

def test_register_duplicate_email(client: TestClient, db_session: Session):
    """Verify that registering with an existing email returns 409 Conflict."""
    payload = {
        "name": "QA User Two",
        "email": "qa_duplicate@cloudhelm.com",
        "password": "StrongPassword123!"
    }
    
    # Register once
    response1 = client.post("/auth/register", json=payload)
    assert response1.status_code == 201
    
    # Register twice
    response2 = client.post("/auth/register", json=payload)
    assert response2.status_code == 409
    assert response2.json()["detail"] == "Email already registered."

def test_login_unapproved_user(client: TestClient, db_session: Session):
    """Verify that a newly registered user cannot login until approved by an admin."""
    # Arrange: Create user directly in db
    payload = {
        "email": "qa_unapproved@cloudhelm.com",
        "password": "TestPassword1!"
    }
    
    user = User(
        name="QA Unapproved User",
        email=payload["email"],
        password_hash=hash_password(payload["password"]),
        is_approved=False
    )
    db_session.add(user)
    db_session.commit()
    
    # Act: Attempt login
    response = client.post("/auth/login", json=payload)
    
    # Assert
    assert response.status_code == 403
    assert response.json()["detail"] == "User pending approval by CloudHelm administrator."

def test_login_successful_and_approved(client: TestClient, db_session: Session):
    """Regression Test (P1): Verify full valid login flow."""
    # Arrange
    payload = {
        "email": "qa_approved@cloudhelm.com",
        "password": "GoodPassword999!"
    }
    
    user = User(
        name="QA Approved User",
        email=payload["email"],
        password_hash=hash_password(payload["password"]),
        is_approved=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Act
    response = client.post("/auth/login", json=payload)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
