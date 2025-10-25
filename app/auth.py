from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from app.config import settings

# Registration auth

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    password = password[:60]
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

#Login auth

def create_token(email: str, user_id: str, role: str) -> str:
    """Create JWT token with user info"""
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    data = {
        "sub": email,
        "user_id": user_id,
        "role": role,
        "exp": expire
    }
    
    token = jwt.encode(data, settings.secret_key, algorithm=settings.algorithm)
    return token

def decode_token(token: str):
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except:
        return None