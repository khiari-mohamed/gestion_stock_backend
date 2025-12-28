"""
Jobs de synchronisation pour le mode offline mobile
"""
from typing import List, Dict
from datetime import datetime
from app.core.database import prisma
import logging

logger = logging.getLogger(__name__)


async def sync_offline_data(user_id: str, sync_data: Dict) -> Dict:
    """
    Synchroniser les données offline du mobile
    
    Args:
        user_id: ID de l'utilisateur
        sync_data: Données à synchroniser (mouvements, ventes, inventaires, etc.)
    
    Returns:
        Résultat de la synchronisation
    """
    synced = {
        "mouvements": 0,
        "articles": 0,
        "ventes": 0,
        "errors": []
    }
    
    # Synchroniser les mouvements de stock
    if "mouvements" in sync_data and sync_data["mouvements"]:
        for mouvement in sync_data["mouvements"]:
            try:
                await prisma.mouvementstock.create(
                    data={
                        "type": mouvement["type"],
                        "article_id": mouvement["article_id"],
                        "magasin_id": mouvement["magasin_id"],
                        "quantite": mouvement["quantite"],
                        "prix_unitaire": mouvement.get("prix_unitaire"),
                        "motif": mouvement.get("motif"),
                        "date_mouvement": mouvement["date_mouvement"],
                        "created_by": user_id
                    }
                )
                synced["mouvements"] += 1
            except Exception as e:
                logger.error(f"Sync error for mouvement: {str(e)}")
                synced["errors"].append(f"Mouvement: {str(e)}")
    
    # Synchroniser les ventes
    if "ventes" in sync_data and sync_data["ventes"]:
        for vente in sync_data["ventes"]:
            try:
                montant_total = vente["quantite"] * vente["prix_unitaire"]
                date_vente = vente["date_vente"]
                
                await prisma.vente.create(
                    data={
                        "article_id": vente["article_id"],
                        "magasin_id": vente["magasin_id"],
                        "quantite": vente["quantite"],
                        "prix_unitaire": vente["prix_unitaire"],
                        "montant_total": montant_total,
                        "date_vente": date_vente,
                        "jour_semaine": date_vente.weekday(),
                        "semaine_annee": date_vente.isocalendar()[1]
                    }
                )
                synced["ventes"] += 1
            except Exception as e:
                logger.error(f"Sync error for vente: {str(e)}")
                synced["errors"].append(f"Vente: {str(e)}")
    
    # Synchroniser les articles modifiés
    if "articles" in sync_data and sync_data["articles"]:
        for article in sync_data["articles"]:
            try:
                await prisma.article.update(
                    where={"id": article["id"]},
                    data=article["data"]
                )
                synced["articles"] += 1
            except Exception as e:
                logger.error(f"Sync error for article: {str(e)}")
                synced["errors"].append(f"Article {article['id']}: {str(e)}")
    
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
    # Articles modifiés
    articles = await prisma.article.find_many(
        where={
            "magasin_id": magasin_id,
            "updated_at": {"gte": last_sync}
        }
    )
    
    # Mouvements récents
    mouvements = await prisma.mouvementstock.find_many(
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
