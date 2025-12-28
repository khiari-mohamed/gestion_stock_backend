from typing import Dict
from datetime import datetime, timedelta
from app.core.database import prisma

class FournisseurScoringService:
    
    @staticmethod
    async def calculate_score(fournisseur_id: str) -> float:
        """Calculer le score de fiabilité d'un fournisseur (0-10)"""
        
        # Récupérer les bons de commande des 6 derniers mois
        date_limite = datetime.now() - timedelta(days=180)
        
        bons = await prisma.boncommande.find_many(
            where={
                "fournisseur_id": fournisseur_id,
                "date_commande": {"gte": date_limite},
                "statut": {"in": ["LIVREE", "PARTIELLEMENT_LIVREE"]}
            }
        )
        
        if not bons:
            return 5.0  # Score neutre par défaut
        
        score = 10.0
        
        # Critère 1: Respect des délais (40% du score)
        retards = 0
        for bon in bons:
            if bon.date_livraison_reelle and bon.date_livraison_prevue:
                if bon.date_livraison_reelle > bon.date_livraison_prevue:
                    retards += 1
        
        taux_retard = retards / len(bons) if bons else 0
        score -= taux_retard * 4.0
        
        # Critère 2: Livraisons complètes (30% du score)
        partielles = sum(1 for b in bons if b.statut == "PARTIELLEMENT_LIVREE")
        taux_partiel = partielles / len(bons) if bons else 0
        score -= taux_partiel * 3.0
        
        # Critère 3: Nombre de commandes (30% du score - fidélité)
        if len(bons) < 3:
            score -= 3.0
        elif len(bons) < 10:
            score -= 1.5
        
        return max(0.0, min(10.0, round(score, 1)))
    
    @staticmethod
    async def update_all_scores() -> Dict:
        """Mettre à jour les scores de tous les fournisseurs"""
        fournisseurs = await prisma.fournisseur.find_many()
        
        updated = 0
        for fournisseur in fournisseurs:
            score = await FournisseurScoringService.calculate_score(fournisseur.id)
            await prisma.fournisseur.update(
                where={"id": fournisseur.id},
                data={"score_fiabilite": score}
            )
            updated += 1
        
        return {"updated": updated, "timestamp": datetime.now()}
    
    @staticmethod
    async def record_price_history(article_id: str, fournisseur_id: str, prix_achat: float):
        """Enregistrer l'historique des prix"""
        await prisma.historiqueprix.create(
            data={
                "article_id": article_id,
                "fournisseur_id": fournisseur_id,
                "prix_achat": prix_achat,
                "date_effet": datetime.now()
            }
        )
    
    @staticmethod
    async def get_price_history(article_id: str, fournisseur_id: str, limit: int = 10):
        """Récupérer l'historique des prix"""
        return await prisma.historiqueprix.find_many(
            where={
                "article_id": article_id,
                "fournisseur_id": fournisseur_id
            },
            order={"date_effet": "desc"},
            take=limit
        )
    
    @staticmethod
    async def get_best_price(article_id: str):
        """Trouver le meilleur prix pour un article"""
        # Récupérer les derniers prix de chaque fournisseur
        historiques = await prisma.historiqueprix.find_many(
            where={"article_id": article_id},
            order={"date_effet": "desc"},
            include={"fournisseur": True}
        )
        
        # Grouper par fournisseur et garder le plus récent
        fournisseurs_prix = {}
        for h in historiques:
            if h.fournisseur_id not in fournisseurs_prix:
                fournisseurs_prix[h.fournisseur_id] = {
                    "fournisseur": h.fournisseur.nom,
                    "prix": h.prix_achat,
                    "date": h.date_effet,
                    "score": h.fournisseur.score_fiabilite
                }
        
        # Trier par prix
        meilleurs = sorted(fournisseurs_prix.values(), key=lambda x: x["prix"])
        
        return meilleurs[:5] if meilleurs else []
