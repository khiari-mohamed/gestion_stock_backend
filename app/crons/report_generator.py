"""
Tâche planifiée pour générer les rapports automatiques
À exécuter via cron: 0 6 1 * * (1er de chaque mois à 6h)
"""
import asyncio
from datetime import datetime
from app.core.database import get_db
from app.jobs.export_jobs import generate_monthly_report, export_for_accountant
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_monthly_reports():
    """Générer les rapports mensuels pour toutes les entreprises"""
    logger.info("Starting monthly report generation...")
    
    db = await get_db()
    
    # Mois précédent
    now = datetime.now()
    month = now.month - 1 if now.month > 1 else 12
    year = now.year if now.month > 1 else now.year - 1
    
    entreprises = await db.entreprise.find_many()
    
    total_reports = 0
    
    for entreprise in entreprises:
        try:
            await generate_monthly_report(entreprise.id, month, year)
            await export_for_accountant(entreprise.id)
            total_reports += 1
            logger.info(f"Reports generated for {entreprise.nom}")
        
        except Exception as e:
            logger.error(f"Error generating reports for {entreprise.nom}: {str(e)}")
    
    logger.info(f"Monthly report generation completed. Total: {total_reports}")
    
    return {"total_reports": total_reports, "month": month, "year": year}


if __name__ == "__main__":
    asyncio.run(generate_monthly_reports())
