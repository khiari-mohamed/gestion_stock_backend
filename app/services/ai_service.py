from typing import List
from datetime import datetime, timedelta
import numpy as np

class AIService:
    """
    Service IA pour la prévision de la demande
    Phase 1 (MVP): Moyenne mobile simple
    Phase 2: Facebook Prophet + modèles avancés
    """
    
    @staticmethod
    async def calculate_prevision_simple(article_id: str, historique_ventes: List[dict]) -> dict:
        """
        Algorithme MVP: Moyenne mobile pondérée
        Phase 2: Remplacer par Prophet ou LightGBM
        """
        if len(historique_ventes) < 4:
            return {
                "quantite_prevue": 0,
                "confiance": 0.3,
                "message": "Données insuffisantes"
            }
        
        # Extraire les quantités des 4 dernières semaines
        quantites = [v["quantite"] for v in historique_ventes[-4:]]
        
        # Moyenne mobile pondérée (plus de poids sur les semaines récentes)
        poids = [0.1, 0.2, 0.3, 0.4]
        prevision = sum(q * p for q, p in zip(quantites, poids))
        
        # Calcul de la confiance basé sur la variance
        variance = np.var(quantites)
        confiance = max(0.3, 1.0 - (variance / 100))
        
        return {
            "quantite_prevue": round(prevision, 2),
            "confiance": min(0.95, confiance),
            "metriques": {
                "mape": None,  # Phase 2
                "wmape": None,  # Phase 2
                "variance": variance
            }
        }
    
    @staticmethod
    async def get_previsions_article(article_id: str, nb_semaines: int = 4):
        """
        Récupérer les prévisions pour un article
        TODO: Implémenter en Phase 2
        """
        pass
    
    @staticmethod
    async def trigger_batch_calculation(magasin_id: str):
        """
        Déclencher le calcul batch des prévisions pour tous les articles
        TODO: Implémenter en Phase 2 avec Celery
        """
        pass
