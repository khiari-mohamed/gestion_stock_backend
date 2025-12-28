from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.database import prisma
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# ============ PASSWORD & TOKEN MANAGEMENT ============

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash using bcrypt"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token with expiration"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token with longer expiration (7 days)"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Decode JWT token with error handling"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré"
        )

# ============ USER & AUTHENTICATION ============

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = decode_token(token)
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )
    
    # Fetch full user object from database
    user = await prisma.user.find_unique(where={"id": user_id})
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur non trouvé ou inactif"
        )
    
    return {
        "id": user.id,
        "email": user.email,
        "nom": user.nom,
        "prenom": user.prenom,
        "role": user.role,
        "langue": user.langue,
        "entreprise_id": user.entreprise_id,
        "is_active": user.is_active
    }

# ============ ROLE-BASED ACCESS CONTROL (RBAC) ============

async def require_role(*allowed_roles: str):
    """Decorator to enforce role-based access control"""
    async def verify_role(current_user: dict = Depends(get_current_user)):
        if current_user.get("role").upper() not in [r.upper() for r in allowed_roles]:
            logger.warning(f"Access denied: User {current_user['id']} with role {current_user['role']} "
                         f"attempted to access endpoint requiring {allowed_roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès refusé. Rôles requis: {', '.join(allowed_roles)}"
            )
        return current_user
    return verify_role

async def require_role_sync(*allowed_roles: str):
    """Synchronous version of require_role for use in decorators"""
    async def verify_role(current_user: dict = Depends(get_current_user)):
        if current_user.get("role").upper() not in [r.upper() for r in allowed_roles]:
            logger.warning(f"Access denied: User {current_user['id']} with role {current_user['role']}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès refusé"
            )
        return current_user
    return verify_role

# ============ TENANT ISOLATION ============

async def verify_user_access_to_enterprise(user: dict, entreprise_id: str) -> bool:
    """Verify that user belongs to the enterprise"""
    return user.get("entreprise_id") == entreprise_id

async def verify_user_access_to_magasin(user: dict, magasin_id: str) -> bool:
    """Verify that magasin belongs to user's enterprise"""
    magasin = await prisma.magasin.find_unique(where={"id": magasin_id})
    if not magasin:
        return False
    return magasin.entreprise_id == user.get("entreprise_id")

async def verify_user_access_to_article(user: dict, article_id: str) -> bool:
    """Verify that article belongs to user's enterprise"""
    article = await prisma.article.find_unique(
        where={"id": article_id},
        include={"magasin": {"select": {"entreprise_id": True}}}
    )
    if not article:
        return False
    return article.magasin.entreprise_id == user.get("entreprise_id")

# ============ HELPER FUNCTIONS ============

def get_role_display_name(role: str) -> str:
    """Get French display name for role"""
    role_names = {
        "PATRON": "Patron/Gérant",
        "GERANT": "Gérant",
        "EMPLOYE": "Employé",
        "COMPTABLE": "Comptable"
    }
    return role_names.get(role.upper(), role)
