from typing import List, Dict
from datetime import datetime, timedelta
from app.core.database import get_db
from app.services.whatsapp_service import WhatsAppService
import logging

logger = logging.getLogger(__name__)


class InventoryService:
    """Service pour gérer les niveaux de stock et générer des alertes"""
    
    def __init__(self):
        self.whatsapp_service = WhatsAppService()
    
    async def check_stock_levels(self, magasin_id: str) -> Dict:
        """
        Vérifier les niveaux de stock et générer des alertes
        
        Returns:
            Dict avec statistiques et alertes générées
        """
        db = await get_db()
        
        # Récupérer tous les articles actifs
        articles = await db.article.find_many(
            where={"magasin_id": magasin_id, "is_active": True}
        )
        
        alertes_generees = []
        ruptures = []
        stock_faible = []
        peremption_proche = []
        
        for article in articles:
            # Vérifier rupture de stock
            if article.stock_actuel == 0:
                ruptures.append(article)
                await self._create_alerte(
                    article_id=article.id,
                    magasin_id=magasin_id,
                    type_alerte="RUPTURE",
                    niveau="CRITIQUE",
                    message=f"Rupture de stock: {article.designation}"
                )
                alertes_generees.append("RUPTURE")
            
            # Vérifier stock faible
            elif article.stock_actuel <= article.stock_min:
                stock_faible.append(article)
                await self._create_alerte(
                    article_id=article.id,
                    magasin_id=magasin_id,
                    type_alerte="SEUIL_BAS",
                    niveau="ELEVE",
                    message=f"Stock faible: {article.designation} ({article.stock_actuel}/{article.stock_min})"
                )
                alertes_generees.append("SEUIL_BAS")
            
            # Vérifier péremption
            if article.date_peremption:
                jours_restants = (article.date_peremption - datetime.now()).days
                if 0 < jours_restants <= 30:
                    peremption_proche.append(article)
                    await self._create_alerte(
                        article_id=article.id,
                        magasin_id=magasin_id,
                        type_alerte="PEREMPTION",
                        niveau="MOYEN" if jours_restants > 7 else "ELEVE",
                        message=f"Péremption proche: {article.designation} (dans {jours_restants} jours)"
                    )
                    alertes_generees.append("PEREMPTION")
        
        return {
            "magasin_id": magasin_id,
            "date_verification": datetime.now(),
            "total_articles": len(articles),
            "ruptures": len(ruptures),
            "stock_faible": len(stock_faible),
            "peremption_proche": len(peremption_proche),
            "alertes_generees": len(alertes_generees)
        }
    
    async def _create_alerte(
        self,
        article_id: str,
        magasin_id: str,
        type_alerte: str,
        niveau: str,
        message: str
    ):
        """Créer une alerte dans la base de données"""
        db = await get_db()
        
        try:
            await db.alerte.create(
                data={
                    "article_id": article_id,
                    "magasin_id": magasin_id,
                    "type": type_alerte,
                    "niveau": niveau,
                    "message": message,
                    "est_vue": False,
                    "est_resolue": False
                }
            )
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
    
    async def calculate_stock_value(self, magasin_id: str) -> Dict:
        """Calculer la valeur totale du stock (Cash immobilisé)"""
        db = await get_db()
        
        articles = await db.article.find_many(
            where={"magasin_id": magasin_id, "is_active": True}
        )
        
        valeur_achat = sum(a.stock_actuel * a.prix_achat for a in articles)
        valeur_vente = sum(a.stock_actuel * a.prix_vente for a in articles)
        marge_potentielle = valeur_vente - valeur_achat
        
        return {
            "magasin_id": magasin_id,
            "valeur_achat_dt": round(valeur_achat, 2),
            "valeur_vente_dt": round(valeur_vente, 2),
            "marge_potentielle_dt": round(marge_potentielle, 2),
            "taux_marge": round((marge_potentielle / valeur_achat * 100) if valeur_achat > 0 else 0, 2),
            "nombre_articles": len(articles)
        }
    
    async def get_slow_moving_items(self, magasin_id: str, days: int = 90) -> List:
        """Identifier les articles à rotation lente (stock dormant)"""
        db = await get_db()
        
        date_limite = datetime.now() - timedelta(days=days)
        
        # Articles sans mouvement récent
        articles = await db.article.find_many(
            where={
                "magasin_id": magasin_id,
                "is_active": True,
                "stock_actuel": {"gt": 0}
            }
        )
        
        slow_items = []
        for article in articles:
            # Vérifier s'il y a eu des mouvements récents
            recent_movements = await db.mouvementstock.count(
                where={
                    "article_id": article.id,
                    "date_mouvement": {"gte": date_limite},
                    "type": "SORTIE"
                }
            )
            
            if recent_movements == 0:
                valeur_immobilisee = article.stock_actuel * article.prix_achat
                slow_items.append({
                    "article": article,
                    "valeur_immobilisee": round(valeur_immobilisee, 2),
                    "jours_sans_mouvement": days
                })
        
        return sorted(slow_items, key=lambda x: x["valeur_immobilisee"], reverse=True)
