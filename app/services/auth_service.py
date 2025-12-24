from typing import Optional
from prisma.models import User
from app.core.database import prisma
from app.core.security import verify_password, get_password_hash, create_access_token
from app.schemas.auth import UserCreate

class AuthService:
    
    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[User]:
        user = await prisma.user.find_unique(where={"email": email})
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
    
    @staticmethod
    async def create_user(data: UserCreate) -> User:
        hashed_password = get_password_hash(data.password)
        return await prisma.user.create(
            data={
                "email": data.email,
                "password_hash": hashed_password,
                "nom": data.nom,
                "prenom": data.prenom,
                "telephone": data.telephone,
                "langue": data.langue,
                "role": data.role,
                "entreprise_id": data.entreprise_id
            }
        )
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[User]:
        return await prisma.user.find_unique(where={"id": user_id})
