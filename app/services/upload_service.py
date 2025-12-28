from fastapi import UploadFile
import os
import uuid
from datetime import datetime
from pathlib import Path

class UploadService:
    UPLOAD_DIR = Path("./uploads")
    DOCUMENTS_DIR = UPLOAD_DIR / "documents"
    IMAGES_DIR = UPLOAD_DIR / "images"
    
    @classmethod
    def _ensure_dirs(cls):
        """Créer les dossiers si nécessaire"""
        cls.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    async def save_document(cls, file: UploadFile, user_id: str) -> str:
        """Sauvegarder un document"""
        cls._ensure_dirs()
        
        ext = file.filename.split(".")[-1].lower()
        filename = f"{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}.{ext}"
        file_path = cls.DOCUMENTS_DIR / filename
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        return f"/uploads/documents/{filename}"
    
    @classmethod
    async def save_article_image(cls, file: UploadFile, user_id: str) -> str:
        """Sauvegarder une image d'article"""
        cls._ensure_dirs()
        
        ext = file.filename.split(".")[-1].lower()
        filename = f"{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}.{ext}"
        file_path = cls.IMAGES_DIR / filename
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        return f"/uploads/images/{filename}"
