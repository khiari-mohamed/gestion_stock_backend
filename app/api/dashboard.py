from fastapi import APIRouter, Depends
from app.services.dashboard_service import DashboardService
from app.core.security import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/magasin/{magasin_id}")
async def get_dashboard_stats(
    magasin_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les statistiques du tableau de bord pour un magasin"""
    stats = await DashboardService.get_dashboard_stats(magasin_id)
    return stats
