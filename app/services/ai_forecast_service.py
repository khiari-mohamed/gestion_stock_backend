"""
Service IA pour la prévision de la demande
Version MVP: Moyenne Mobile Pondérée
"""
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from app.core.database import get_db
import numpy as np
import logging

logger = logging.getLogger(__name__)


class AIForecastService:
    """Service de prévision IA basé sur l'historique des ventes"""
    
    def __init__(self):
        self.version_modele = "1.0"
        self.algorithme = "moving_average"
    
    async def generate_forecast(
        self,
        article_id: str,
        magasin_id: str,
        horizon_jours: int = 7
    ) -> Optional[Dict]:
        """
        Générer une prévision pour un article
        
        Args:
            article_id: ID de l'article
            magasin_id: ID du magasin
            horizon_jours: Nombre de jours à prévoir (défaut: 7)
        
        Returns:
            Dict avec prévision ou None si données insuffisantes
        """
        db = await get_db()
        
        # Récupérer l'historique des ventes (4 dernières semaines minimum)
        date_debut = datetime.now() - timedelta(weeks=8)
        
        ventes = await db.vente.find_many(
            where={
                "article_id": article_id,
                "magasin_id": magasin_id,
                "date_vente": {"gte": date_debut}
            },
            order={"date_vente": "asc"}
        )
        
        if len(ventes) < 4:
            logger.warning(f"Insufficient data for article {article_id}: {len(ventes)} sales")
            return None
        
        # Calculer la prévision avec moyenne mobile pondérée
        quantites = [v.quantite for v in ventes]
        
        # Pondération: plus récent = plus important
        weights = np.linspace(0.5, 1.0, len(quantites))
        quantite_prevue = np.average(quantites, weights=weights)
        
        # Calculer le niveau de confiance basé sur la variance
        variance = np.var(quantites)
        confiance = max(0.3, min(0.95, 1.0 - (variance / 100)))
        
        # Calculer les métriques
        metriques = self._calculate_metrics(quantites, quantite_prevue)
        
        # Période de prévision
        date_periode = datetime.now() + timedelta(days=1)
        date_fin_periode = date_periode + timedelta(days=horizon_jours)
        
        # Sauvegarder la prévision
        prevision = await db.prevision.upsert(
            where={
                "article_id_magasin_id_date_periode": {
                    "article_id": article_id,
                    "magasin_id": magasin_id,
                    "date_periode": date_periode
                }
            },
            data={
                "create": {
                    "article_id": article_id,
                    "magasin_id": magasin_id,
                    "date_periode": date_periode,
                    "date_fin_periode": date_fin_periode,
                    "quantite_prevue": round(quantite_prevue, 2),
                    "confiance": round(confiance, 2),
                    "algorithme": self.algorithme,
                    "version_modele": self.version_modele,
                    "metriques": metriques
                },
                "update": {
                    "quantite_prevue": round(quantite_prevue, 2),
                    "confiance": round(confiance, 2),
                    "metriques": metriques,
                    "date_calcul": datetime.now()
                }
            }
        )
        
        return {
            "article_id": article_id,
            "quantite_prevue": round(quantite_prevue, 2),
            "confiance": round(confiance, 2),
            "periode": f"{horizon_jours} jours",
            "metriques": metriques
        }
    
    def _calculate_metrics(self, historique: List[float], prevision: float) -> Dict:
        """Calculer les métriques de performance"""
        if not historique:
            return {}
        
        # MAPE (Mean Absolute Percentage Error)
        mape = np.mean([abs((h - prevision) / h) for h in historique if h > 0]) * 100
        
        # WMAPE (Weighted MAPE)
        total_actual = sum(historique)
        total_error = sum([abs(h - prevision) for h in historique])
        wmape = (total_error / total_actual * 100) if total_actual > 0 else 0
        
        # Coverage (pourcentage de données utilisées)
        coverage = (len(historique) / 28) * 100  # 28 jours = 4 semaines
        
        return {
            "mape": round(mape, 2),
            "wmape": round(wmape, 2),
            "coverage": round(min(coverage, 100), 2),
            "nb_points": len(historique)
        }
    
    async def get_purchase_suggestions(self, magasin_id: str) -> List[Dict]:
        """
        Générer des suggestions de commande basées sur les prévisions
        
        Returns:
            Liste d'articles à commander avec quantités suggérées
        """
        db = await get_db()
        
        # Récupérer les articles avec prévisions récentes
        date_limite = datetime.now() - timedelta(days=1)
        
        previsions = await db.prevision.find_many(
            where={
                "magasin_id": magasin_id,
                "date_calcul": {"gte": date_limite}
            },
            include={"article": True}
        )
        
        suggestions = []
        
        for prev in previsions:
            article = prev.article
            
            # Calculer la quantité à commander
            stock_actuel = article.stock_actuel
            demande_prevue = prev.quantite_prevue
            stock_securite = article.stock_securite
            
            # Quantité nécessaire = demande prévue + stock sécurité - stock actuel
            quantite_necessaire = demande_prevue + stock_securite - stock_actuel
            
            if quantite_necessaire > 0:
                suggestions.append({
                    "article_id": article.id,
                    "code": article.code,
                    "designation": article.designation,
                    "stock_actuel": stock_actuel,
                    "demande_prevue": round(demande_prevue, 0),
                    "quantite_a_commander": round(quantite_necessaire, 0),
                    "confiance": prev.confiance,
                    "priorite": "HAUTE" if stock_actuel <= article.stock_min else "NORMALE"
                })
        
        # Trier par priorité et stock actuel
        suggestions.sort(key=lambda x: (x["priorite"] == "HAUTE", -x["stock_actuel"]), reverse=True)
        
        return suggestions
