from fastapi import APIRouter, HTTPException, status
from app.api.v1.models.schemas import UserLogin, Token, UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.core.security import create_access_token

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Connexion utilisateur"""
    user = await AuthService.authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    access_token = create_access_token(data={"sub": user.id, "role": user.role})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate):
    """Créer un nouveau compte utilisateur"""
    try:
        user = await AuthService.create_user(data)
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
