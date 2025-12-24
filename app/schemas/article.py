from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ArticleBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    designation: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    code_barre: Optional[str] = None
    unite: str = "unite"
    prix_achat: float = Field(default=0, ge=0)
    prix_vente: float = Field(default=0, ge=0)
    stock_min: int = Field(default=0, ge=0)
    stock_max: int = Field(default=100, ge=0)
    date_peremption: Optional[datetime] = None

class ArticleCreate(ArticleBase):
    magasin_id: str

class ArticleUpdate(BaseModel):
    designation: Optional[str] = None
    description: Optional[str] = None
    code_barre: Optional[str] = None
    unite: Optional[str] = None
    prix_achat: Optional[float] = Field(None, ge=0)
    prix_vente: Optional[float] = Field(None, ge=0)
    stock_min: Optional[int] = Field(None, ge=0)
    stock_max: Optional[int] = Field(None, ge=0)
    date_peremption: Optional[datetime] = None
    is_active: Optional[bool] = None

class ArticleResponse(ArticleBase):
    id: str
    stock_actuel: int
    is_active: bool
    magasin_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
