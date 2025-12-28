from typing import List, Optional
from datetime import datetime
from prisma.models import Vente
from app.core.database import prisma
from app.schemas.vente import VenteCreate

class VenteService:
    
    @staticmethod
    async def create_vente(data: VenteCreate) -> Vente:
        """Créer une vente et déduire du stock"""
        montant_total = data.quantite * data.prix_unitaire
        jour_semaine = data.date_vente.weekday()
        semaine_annee = data.date_vente.isocalendar()[1]
        
        vente = await prisma.vente.create(
            data={
                "article_id": data.article_id,
                "magasin_id": data.magasin_id,
                "quantite": data.quantite,
                "prix_unitaire": data.prix_unitaire,
                "montant_total": montant_total,
                "date_vente": data.date_vente,
                "jour_semaine": jour_semaine,
                "semaine_annee": semaine_annee
            }
        )
        
        # Déduire du stock
        await prisma.article.update(
            where={"id": data.article_id},
            data={"stock_actuel": {"decrement": data.quantite}}
        )
        
        # Créer mouvement de sortie
        await prisma.mouvementstock.create(
            data={
                "type": "SORTIE",
                "quantite": data.quantite,
                "prix_unitaire": data.prix_unitaire,
                "valeur_totale": montant_total,
                "motif": "Vente",
                "article_id": data.article_id,
                "magasin_id": data.magasin_id,
                "date_mouvement": data.date_vente
            }
        )
        
        return vente
    
    @staticmethod
    async def create_ventes_bulk(ventes: List[VenteCreate]) -> dict:
        """Créer plusieurs ventes en batch"""
        created = []
        errors = []
        
        for vente_data in ventes:
            try:
                vente = await VenteService.create_vente(vente_data)
                created.append(vente.id)
            except Exception as e:
                errors.append({"article_id": vente_data.article_id, "error": str(e)})
        
        return {"created": len(created), "errors": errors}
    
    @staticmethod
    async def get_ventes_by_article(
        article_id: str,
        date_debut: Optional[datetime] = None,
        date_fin: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Vente]:
        """Récupérer les ventes d'un article"""
        where = {"article_id": article_id}
        
        if date_debut or date_fin:
            where["date_vente"] = {}
            if date_debut:
                where["date_vente"]["gte"] = date_debut
            if date_fin:
                where["date_vente"]["lte"] = date_fin
        
        return await prisma.vente.find_many(
            where=where,
            order={"date_vente": "desc"},
            take=limit
        )
    
    @staticmethod
    async def get_ventes_stats(
        magasin_id: str,
        date_debut: Optional[datetime] = None,
        date_fin: Optional[datetime] = None
    ) -> dict:
        """Statistiques de ventes"""
        where = {"magasin_id": magasin_id}
        
        if date_debut or date_fin:
            where["date_vente"] = {}
            if date_debut:
                where["date_vente"]["gte"] = date_debut
            if date_fin:
                where["date_vente"]["lte"] = date_fin
        
        ventes = await prisma.vente.find_many(where=where)
        
        total_ventes = sum(v.montant_total for v in ventes)
        total_quantite = sum(v.quantite for v in ventes)
        
        return {
            "total_ventes_dt": round(total_ventes, 3),
            "total_quantite": total_quantite,
            "nombre_transactions": len(ventes),
            "panier_moyen": round(total_ventes / len(ventes), 3) if ventes else 0
        }
