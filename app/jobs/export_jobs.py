"""
Jobs d'export en arrière-plan
"""
from datetime import datetime
from app.core.database import get_db
from app.services.export_service import ExportService
import logging

logger = logging.getLogger(__name__)


async def generate_monthly_report(entreprise_id: str, month: int, year: int):
    """Générer le rapport mensuel automatique"""
    db = await get_db()
    export_service = ExportService()
    
    magasins = await db.magasin.find_many(
        where={"entreprise_id": entreprise_id}
    )
    
    for magasin in magasins:
        try:
            # Récupérer les données du mois
            mouvements = await db.mouvementstock.find_many(
                where={
                    "magasin_id": magasin.id,
                    "date_mouvement": {
                        "gte": datetime(year, month, 1),
                        "lt": datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
                    }
                },
                include={"article": True}
            )
            
            # Générer l'export
            excel_buffer = export_service.export_mouvements_excel(mouvements)
            
            # Sauvegarder ou envoyer par email
            logger.info(f"Monthly report generated for magasin {magasin.code}")
            
        except Exception as e:
            logger.error(f"Error generating report for {magasin.code}: {str(e)}")


async def export_for_accountant(entreprise_id: str):
    """Générer l'export comptable mensuel"""
    db = await get_db()
    export_service = ExportService()
    
    magasins = await db.magasin.find_many(
        where={"entreprise_id": entreprise_id}
    )
    
    for magasin in magasins:
        articles = await db.article.find_many(
            where={"magasin_id": magasin.id, "is_active": True}
        )
        
        excel_buffer = export_service.export_valorisation_excel(articles)
        
        logger.info(f"Accounting export generated for {magasin.code}")
