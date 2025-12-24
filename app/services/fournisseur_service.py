from typing import List, Optional
from prisma.models import Fournisseur
from app.core.database import prisma
from app.api.v1.models.schemas import FournisseurCreate, FournisseurUpdate

class FournisseurService:
    
    @staticmethod
    async def create_fournisseur(data: FournisseurCreate) -> Fournisseur:
        return await prisma.fournisseur.create(
            data={
                "nom": data.nom,
                "type": data.type,
                "telephone": data.telephone,
                "email": data.email,
                "adresse": data.adresse,
                "matricule_fiscal": data.matricule_fiscal,
                "delai_livraison": data.delai_livraison,
                "entreprise_id": data.entreprise_id
            }
        )
    
    @staticmethod
    async def get_fournisseur(fournisseur_id: str) -> Optional[Fournisseur]:
        return await prisma.fournisseur.find_unique(where={"id": fournisseur_id})
    
    @staticmethod
    async def get_fournisseurs_by_entreprise(entreprise_id: str, skip: int = 0, limit: int = 100) -> List[Fournisseur]:
        return await prisma.fournisseur.find_many(
            where={"entreprise_id": entreprise_id},
            skip=skip,
            take=limit,
            order={"nom": "asc"}
        )
    
    @staticmethod
    async def update_fournisseur(fournisseur_id: str, data: FournisseurUpdate) -> Optional[Fournisseur]:
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await FournisseurService.get_fournisseur(fournisseur_id)
        
        return await prisma.fournisseur.update(
            where={"id": fournisseur_id},
            data=update_data
        )
    
    @staticmethod
    async def delete_fournisseur(fournisseur_id: str) -> bool:
        await prisma.fournisseur.delete(where={"id": fournisseur_id})
        return True
