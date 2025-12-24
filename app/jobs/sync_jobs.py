"""
Jobs de synchronisation pour le mode offline mobile
"""
from typing import List, Dict
from datetime import datetime
from app.core.database import get_db
import logging

logger = logging.getLogger(__name__)


async def sync_offline_data(user_id: str, sync_data: Dict) -> Dict:
    """
    Synchroniser les données offline du mobile
    
    Args:
        user_id: ID de l'utilisateur
        sync_data: Données à synchroniser (mouvements, inventaires, etc.)
    
    Returns:
        Résultat de la synchronisation
    """
    db = await get_db()
    
    synced = {
        "mouvements": 0,
        "articles": 0,
        "errors": []
    }
    
    # Synchroniser les mouvements de stock
    if "mouvements" in sync_data:
        for mouvement in sync_data["mouvements"]:
            try:
                await db.mouvementstock.create(
                    data={
                        **mouvement,
                        "created_by": user_id,
                        "created_at": datetime.now()
                    }
                )
                synced["mouvements"] += 1
            except Exception as e:
                logger.error(f"Sync error for mouvement: {str(e)}")
                synced["errors"].append(str(e))
    
    # Synchroniser les articles modifiés
    if "articles" in sync_data:
        for article in sync_data["articles"]:
            try:
                await db.article.update(
                    where={"id": article["id"]},
                    data=article["data"]
                )
                synced["articles"] += 1
            except Exception as e:
                logger.error(f"Sync error for article: {str(e)}")
                synced["errors"].append(str(e))
    
    return synced


async def get_sync_data(magasin_id: str, last_sync: datetime) -> Dict:
    """
    Récupérer les données modifiées depuis la dernière sync
    
    Args:
        magasin_id: ID du magasin
        last_sync: Date de la dernière synchronisation
    
    Returns:
        Données à synchroniser vers le mobile
    """
    db = await get_db()
    
    # Articles modifiés
    articles = await db.article.find_many(
        where={
            "magasin_id": magasin_id,
            "updated_at": {"gte": last_sync}
        }
    )
    
    # Mouvements récents
    mouvements = await db.mouvementstock.find_many(
        where={
            "magasin_id": magasin_id,
            "created_at": {"gte": last_sync}
        }
    )
    
    return {
        "articles": articles,
        "mouvements": mouvements,
        "sync_timestamp": datetime.now()
    }
