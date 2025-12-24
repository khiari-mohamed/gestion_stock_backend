from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.api.v1.models.schemas import RapportRequest
from app.services.report_service import ReportService
from app.core.security import get_current_user

router = APIRouter()

@router.post("/generate")
async def generate_rapport(
    data: RapportRequest,
    current_user: dict = Depends(get_current_user)
):
    """Générer un rapport (PDF ou Excel) - Phase 2"""
    # TODO: Implémenter en Phase 2
    return {"message": "Génération de rapport (Phase 2)", "type": data.type, "format": data.format}

@router.get("/download/{rapport_id}")
async def download_rapport(
    rapport_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Télécharger un rapport généré - Phase 2"""
    # TODO: Implémenter en Phase 2
    raise HTTPException(status_code=501, detail="Fonctionnalité Phase 2")
