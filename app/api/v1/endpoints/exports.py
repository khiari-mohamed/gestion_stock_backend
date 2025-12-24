from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.export_service import ExportService
from datetime import datetime
import io

router = APIRouter(prefix="/exports", tags=["Exports"])


@router.get("/mouvements/excel")
async def export_mouvements_excel(
    magasin_id: str,
    date_debut: datetime = None,
    date_fin: datetime = None,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Exporter les mouvements en Excel"""
    where = {"magasin_id": magasin_id}
    if date_debut and date_fin:
        where["date_mouvement"] = {"gte": date_debut, "lte": date_fin}
    
    mouvements = await db.mouvementstock.find_many(
        where=where,
        include={"article": True}
    )
    
    export_service = ExportService()
    excel_buffer = export_service.export_mouvements_excel(mouvements)
    
    return StreamingResponse(
        io.BytesIO(excel_buffer),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=mouvements_{datetime.now().strftime('%Y%m%d')}.xlsx"}
    )


@router.get("/stock/pdf")
async def export_stock_pdf(
    magasin_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Exporter l'état du stock en PDF"""
    articles = await db.article.find_many(
        where={"magasin_id": magasin_id, "is_active": True}
    )
    
    export_service = ExportService()
    pdf_buffer = export_service.export_stock_pdf(articles, magasin_id)
    
    return StreamingResponse(
        io.BytesIO(pdf_buffer),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=stock_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )


@router.get("/valorisation/excel")
async def export_valorisation_excel(
    magasin_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Exporter la valorisation du stock (comptabilité tunisienne)"""
    articles = await db.article.find_many(
        where={"magasin_id": magasin_id, "is_active": True}
    )
    
    export_service = ExportService()
    excel_buffer = export_service.export_valorisation_excel(articles)
    
    return StreamingResponse(
        io.BytesIO(excel_buffer),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=valorisation_{datetime.now().strftime('%Y%m%d')}.xlsx"}
    )
