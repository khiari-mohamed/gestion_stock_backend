from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.services.upload_service import UploadService
from app.core.security import get_current_user
import os

router = APIRouter(prefix="/uploads", tags=["Uploads"])

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload document photo (bon de livraison, facture)"""
    
    # Validate extension
    ext = file.filename.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Extension non autorisée. Autorisé: {ALLOWED_EXTENSIONS}")
    
    # Validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 10MB)")
    
    await file.seek(0)
    
    # Save file
    file_path = await UploadService.save_document(file, current_user["sub"])
    
    return {
        "filename": file.filename,
        "url": file_path,
        "size": len(content)
    }

@router.post("/article-image")
async def upload_article_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload article image"""
    
    ext = file.filename.split(".")[-1].lower()
    if ext not in {"jpg", "jpeg", "png"}:
        raise HTTPException(status_code=400, detail="Format image non autorisé")
    
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Image trop volumineuse (max 10MB)")
    
    await file.seek(0)
    
    file_path = await UploadService.save_article_image(file, current_user["sub"])
    
    return {
        "filename": file.filename,
        "url": file_path,
        "size": len(content)
    }
