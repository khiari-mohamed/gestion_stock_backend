"""
Tâche planifiée pour générer les alertes automatiques
À exécuter via cron: */30 * * * * (toutes les 30 minutes)
"""
import asyncio
from datetime import datetime
from app.core.database import get_db
from app.services.inventory_service import InventoryService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_alerts():
    """Vérifier les stocks et générer les alertes nécessaires"""
    logger.info("Starting alert generation...")
    
    db = await get_db()
    inventory_service = InventoryService()
    
    magasins = await db.magasin.find_many()
    
    total_alerts = 0
    
    for magasin in magasins:
        try:
            result = await inventory_service.check_stock_levels(magasin.id)
            total_alerts += result["alertes_generees"]
            logger.info(f"Magasin {magasin.code}: {result['alertes_generees']} alertes générées")
        
        except Exception as e:
            logger.error(f"Error generating alerts for {magasin.code}: {str(e)}")
    
    logger.info(f"Alert generation completed. Total alerts: {total_alerts}")
    
    return {"total_alerts": total_alerts, "timestamp": datetime.now()}


if __name__ == "__main__":
    asyncio.run(generate_alerts())
