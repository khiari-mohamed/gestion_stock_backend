from fastapi import APIRouter, HTTPException, status, Body
from datetime import timedelta
from app.api.v1.models.schemas import (
    UserLogin, Token, UserCreate, UserResponse, 
    TokenRefresh, PasswordReset, PasswordResetConfirm
)
from app.services.auth_service import AuthService
from app.core.security import (
    create_access_token, create_refresh_token, 
    get_password_hash, verify_password
)
from app.core.database import prisma
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Login endpoint - Authenticate user and return JWT tokens
    
    Returns:
        - access_token: JWT for API requests (30 mins)
        - refresh_token: JWT for token refresh (7 days)
        - user: User object with metadata
    """
    user = await AuthService.authenticate_user(credentials.email, credentials.password)
    if not user:
        logger.warning(f"Failed login attempt for email: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    # Update last login timestamp
    await prisma.user.update(
        where={"id": user.id},
        data={"last_login": prisma.get_current_timestamp()}
    )
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role},
        expires_delta=timedelta(minutes=30)
    )
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 1800,  # 30 minutes in seconds
        "user": {
            "id": user.id,
            "email": user.email,
            "nom": user.nom,
            "prenom": user.prenom,
            "role": user.role,
            "entreprise_id": user.entreprise_id,
            "langue": user.langue
        }
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh):
    """
    Refresh access token using refresh token
    
    Refresh tokens are valid for 7 days
    """
    try:
        from app.core.security import decode_token
        
        payload = decode_token(token_data.refresh_token)
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
        
        user_id = payload.get("sub")
        user = await prisma.user.find_unique(where={"id": user_id})
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisateur non trouvé"
            )
        
        # Generate new access token
        new_access_token = create_access_token(
            data={"sub": user.id, "role": user.role},
            expires_delta=timedelta(minutes=30)
        )
        
        return {
            "access_token": new_access_token,
            "refresh_token": token_data.refresh_token,  # Refresh token stays same
            "token_type": "bearer",
            "expires_in": 1800,
            "user": {
                "id": user.id,
                "email": user.email,
                "nom": user.nom,
                "prenom": user.prenom,
                "role": user.role,
                "entreprise_id": user.entreprise_id,
                "langue": user.langue
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate):
    """
    Register new user
    
    Creates new user and links to enterprise
    """
    try:
        # Verify enterprise exists
        entreprise = await prisma.entreprise.find_unique(
            where={"id": data.entreprise_id}
        )
        if not entreprise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entreprise non trouvée"
            )
        
        # Check if email already exists
        existing = await prisma.user.find_unique(where={"email": data.email})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cet email est déjà utilisé"
            )
        
        user = await AuthService.create_user(data)
        return {
            "id": user.id,
            "email": user.email,
            "nom": user.nom,
            "prenom": user.prenom,
            "telephone": user.telephone,
            "langue": user.langue,
            "role": user.role,
            "entreprise_id": user.entreprise_id,
            "is_active": user.is_active,
            "created_at": user.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur lors de l'enregistrement"
        )


@router.post("/forgot-password")
async def forgot_password(email: str = Body(...)):
    """
    Request password reset
    
    Sends reset link to email (Phase 2 implementation)
    """
    user = await prisma.user.find_unique(where={"email": email})
    
    if not user:
        # Don't reveal if email exists (security)
        return {"message": "Si cet email existe, vous recevrez un lien de réinitialisation"}
    
    try:
        # TODO: Phase 2 - Generate reset token and send email
        # For now, just log the request
        logger.info(f"Password reset requested for: {email}")
        
        return {
            "message": "Lien de réinitialisation envoyé par email",
            "email": email
        }
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la réinitialisation"
        )


@router.post("/reset-password")
async def reset_password(data: PasswordResetConfirm):
    """
    Reset password with token
    
    Requires valid reset token from email
    """
    try:
        # TODO: Phase 2 - Validate reset token and update password
        # For now, placeholder
        return {
            "message": "Mot de passe réinitialisé",
            "email": data.email
        }
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lien de réinitialisation invalide ou expiré"
        )


@router.post("/change-password")
async def change_password(
    current_user: dict,
    old_password: str = Body(...),
    new_password: str = Body(...)
):
    """
    Change password for authenticated user
    """
    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe doit contenir au moins 6 caractères"
        )
    
    user = await prisma.user.find_unique(where={"id": current_user["id"]})
    
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ancien mot de passe incorrect"
        )
    
    # Update password
    new_hash = get_password_hash(new_password)
    await prisma.user.update(
        where={"id": user.id},
        data={"password_hash": new_hash}
    )
    
    logger.info(f"Password changed for user: {user.email}")
    
    return {"message": "Mot de passe modifié avec succès"}

