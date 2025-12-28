import asyncio
from datetime import datetime, timedelta
from app.core.database import prisma
from app.services.ai_forecast_service import AIForecastService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_daily_forecasts():
    """Générer les prévisions pour tous les articles éligibles"""
    logger.info("Starting daily forecast generation...")
    
    await prisma.connect()
    ai_service = AIForecastService()
    
    magasins = await prisma.magasin.find_many()
    
    total_forecasts = 0
    errors = 0
    
    for magasin in magasins:
        try:
            articles = await prisma.article.find_many(
                where={"magasin_id": magasin.id, "is_active": True}
            )
            
            for article in articles:
                try:
                    date_limite = datetime.now() - timedelta(weeks=4)
                    ventes_count = await prisma.vente.count(
                        where={
                            "article_id": article.id,
                            "date_vente": {"gte": date_limite}
                        }
                    )
                    
                    if ventes_count >= 4:
                        forecast = await ai_service.generate_forecast(
                            article_id=article.id,
                            magasin_id=magasin.id
                        )
                        
                        if forecast:
                            total_forecasts += 1
                    
                except Exception as e:
                    logger.error(f"Error forecasting article {article.code}: {str(e)}")
                    errors += 1
        
        except Exception as e:
            logger.error(f"Error processing magasin {magasin.code}: {str(e)}")
            errors += 1
    
    logger.info(f"Forecast generation completed. Total: {total_forecasts}, Errors: {errors}")
    
    await prisma.disconnect()
    
    return {"total_forecasts": total_forecasts, "errors": errors, "timestamp": datetime.now()}


if __name__ == "__main__":
    asyncio.run(generate_daily_forecasts())
