from flask import request
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import secrets

import database

# Google OAuth Client ID (must match frontend)
GOOGLE_CLIENT_ID = "693422158799-3b30id9m2eo0l4463m4njruokbalk5bd.apps.googleusercontent.com"


def _generate_api_token() -> str:
    return secrets.token_urlsafe(32)


def verify_google_token(token: str) -> dict:
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
        
        # Token is valid, extract user info
        return {
            "google_id": idinfo["sub"],
            "email": idinfo["email"],
            "name": idinfo.get("name", idinfo["email"].split("@")[0])
        }
    except ValueError as e:
        print(f"Google token verification failed: {e}")
        return None


def check_auth(req: request) -> dict:
    auth_header = req.headers.get('Authorization')
    if not auth_header:
        return {"error": (401, 'Missing Authorization Header')}
    
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != 'bearer':
            return {"error": (401, 'Invalid Authorization Scheme')}
    except ValueError:
        return {"error": (401, 'Invalid Authorization Header')}
    
    user = database.get_user_by_token(token)
    if not user:
        return {"error": (401, 'Invalid Token')}
    
    # Return user data in compatible format
    return {
        "id": user.id,
        "token": user.api_token,
        "name": user.name,
        "email": user.email,
        "profile_completed": user.profile_completed
    }


def check_auth_ws(token: str) -> bool:
    user = database.get_user_by_token(token)
    return user is not None


def login(google_token: str) -> dict:
    # Verify Google token
    google_user = verify_google_token(google_token)
    if not google_user:
        return {"error": "Invalid Google token"}
    
    google_id = google_user["google_id"]
    email = google_user["email"]
    name = google_user["name"]
    
    # Check if user exists
    user = database.User.query.filter_by(google_id=google_id).first()
    is_new_user = user is None
    
    if is_new_user:
        # Create new user
        api_token = _generate_api_token()
        user = database.create_user(
            google_id=google_id,
            email=email,
            name=name,
            api_token=api_token
        )
        print(f"Created new user: {email}")
    else:
        print(f"Existing user logged in: {email}")
    
    return {
        "api_token": user.api_token,
        "is_new_user": is_new_user,
        "user": {
            "name": user.name,
            "email": user.email,
            "token": user.api_token
        }
    }