from fastapi import APIRouter, Depends
from typing import Dict
from datetime import datetime
from app.schemas.sync import SyncRequest, SyncResponse
from app.jobs.sync_jobs import sync_offline_data, get_sync_data
from app.core.security import get_current_user

router = APIRouter(prefix="/sync", tags=["Synchronisation"])

@router.post("/upload", response_model=SyncResponse)
async def sync_upload(
    data: SyncRequest,
    current_user: dict = Depends(get_current_user)
):
    """Synchroniser les données offline du mobile vers le serveur"""
    result = await sync_offline_data(current_user["sub"], data.dict())
    
    return SyncResponse(
        success=len(result["errors"]) == 0,
        mouvements_synced=result["mouvements"],
        articles_synced=result["articles"],
        ventes_synced=result.get("ventes", 0),
        errors=result["errors"],
        timestamp=datetime.now()
    )

@router.get("/download")
async def sync_download(
    magasin_id: str,
    last_sync: datetime,
    current_user: dict = Depends(get_current_user)
):
    """Télécharger les données modifiées depuis la dernière sync"""
    data = await get_sync_data(magasin_id, last_sync)
    
    return {
        "articles": [
            {
                "id": a.id,
                "code": a.code,
                "designation": a.designation,
                "stock_actuel": a.stock_actuel,
                "prix_vente": a.prix_vente,
                "updated_at": a.updated_at
            }
            for a in data["articles"]
        ],
        "mouvements": [
            {
                "id": m.id,
                "type": m.type,
                "article_id": m.article_id,
                "quantite": m.quantite,
                "date_mouvement": m.date_mouvement
            }
            for m in data["mouvements"]
        ],
        "sync_timestamp": data["sync_timestamp"]
    }
