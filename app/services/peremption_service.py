from typing import List, Dict
from datetime import datetime, timedelta
from app.core.database import prisma

class PeremptionService:
    
    @staticmethod
    async def check_peremptions(magasin_id: str, jours_alerte: int = 30) -> Dict:
        """Vérifier les articles proches de la péremption"""
        
        date_limite = datetime.now() + timedelta(days=jours_alerte)
        
        articles = await prisma.article.find_many(
            where={
                "magasin_id": magasin_id,
                "is_active": True,
                "date_peremption": {
                    "lte": date_limite,
                    "gte": datetime.now()
                }
            },
            order={"date_peremption": "asc"}
        )
        
        alertes = []
        for article in articles:
            jours_restants = (article.date_peremption - datetime.now()).days
            
            niveau = "CRITIQUE" if jours_restants <= 7 else "ELEVE" if jours_restants <= 14 else "MOYEN"
            
            alertes.append({
                "article_id": article.id,
                "code": article.code,
                "designation": article.designation,
                "stock_actuel": article.stock_actuel,
                "date_peremption": article.date_peremption,
                "jours_restants": jours_restants,
                "niveau": niveau,
                "valeur_risque": round(article.stock_actuel * article.prix_achat, 3)
            })
            
            # Créer alerte si pas déjà existante
            existing = await prisma.alerte.find_first(
                where={
                    "article_id": article.id,
                    "type": "PEREMPTION",
                    "est_resolue": False
                }
            )
            
            if not existing:
                await prisma.alerte.create(
                    data={
                        "article_id": article.id,
                        "magasin_id": magasin_id,
                        "type": "PEREMPTION",
                        "niveau": niveau,
                        "message": f"Péremption dans {jours_restants} jours: {article.designation}",
                        "est_vue": False,
                        "est_resolue": False
                    }
                )
        
        return {
            "total_articles": len(alertes),
            "valeur_totale_risque": sum(a["valeur_risque"] for a in alertes),
            "alertes": alertes
        }
    
    @staticmethod
    async def get_fifo_order(article_id: str) -> List:
        """Obtenir l'ordre FIFO pour un article (plus ancien en premier)"""
        # Pour MVP, on utilise la date de péremption
        # En production, il faudrait tracker les lots
        article = await prisma.article.find_unique(where={"id": article_id})
        
        if not article or not article.date_peremption:
            return []
        
        return [{
            "article_id": article.id,
            "date_peremption": article.date_peremption,
            "quantite": article.stock_actuel,
            "ordre": "FIFO"
        }]
    
    @staticmethod
    async def suggest_actions(magasin_id: str) -> List[Dict]:
        """Suggérer des actions pour les articles proches de péremption"""
        result = await PeremptionService.check_peremptions(magasin_id, 30)
        
        suggestions = []
        for alerte in result["alertes"]:
            if alerte["jours_restants"] <= 7:
                action = "PROMOTION_URGENTE"
                message = f"Promotion -50% recommandée pour écouler le stock"
            elif alerte["jours_restants"] <= 14:
                action = "PROMOTION"
                message = f"Promotion -30% recommandée"
            else:
                action = "SURVEILLANCE"
                message = f"Surveiller les ventes"
            
            suggestions.append({
                **alerte,
                "action_recommandee": action,
                "message": message
            })
        
        return suggestions
