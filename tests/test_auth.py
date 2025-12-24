import pytest
from app.core.security import get_password_hash, verify_password, create_access_token, decode_token

def test_password_hashing():
    """Test du hashage et de la vérification des mots de passe"""
    password = "password123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_jwt_token_creation_and_decode():
    """Test de la création et du décodage des tokens JWT"""
    data = {"sub": "user123", "role": "patron"}
    token = create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    
    decoded = decode_token(token)
    assert decoded["sub"] == "user123"
    assert decoded["role"] == "patron"
    assert "exp" in decoded
