from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# ============================================
# AUTH SCHEMAS
# ============================================

class UserBase(BaseModel):
    email: EmailStr
    nom: str = Field(..., min_length=1, max_length=100)
    prenom: str = Field(..., min_length=1, max_length=100)
    telephone: Optional[str] = None
    langue: str = Field(default="fr", pattern="^(fr|ar)$")
    role: str = Field(default="employe", pattern="^(patron|employe|comptable)$")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    entreprise_id: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: str
    entreprise_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ============================================
# ARTICLE SCHEMAS
# ============================================

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

# ============================================
# MOUVEMENT STOCK SCHEMAS
# ============================================

class MouvementStockBase(BaseModel):
    type: str = Field(..., pattern="^(entree|sortie|ajustement|retour)$")
    quantite: int = Field(..., gt=0)
    prix_unitaire: Optional[float] = Field(None, ge=0)
    motif: Optional[str] = None
    reference_doc: Optional[str] = None
    date_mouvement: Optional[datetime] = None

class MouvementStockCreate(MouvementStockBase):
    article_id: str
    magasin_id: str
    fournisseur_id: Optional[str] = None

class MouvementStockResponse(MouvementStockBase):
    id: str
    article_id: str
    magasin_id: str
    fournisseur_id: Optional[str]
    photo_doc_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ============================================
# FOURNISSEUR SCHEMAS
# ============================================

class FournisseurBase(BaseModel):
    nom: str = Field(..., min_length=1, max_length=200)
    type: str = Field(default="formel", pattern="^(formel|informel)$")
    telephone: Optional[str] = None
    email: Optional[EmailStr] = None
    adresse: Optional[str] = None
    matricule_fiscal: Optional[str] = None
    delai_livraison: Optional[int] = Field(None, ge=0)

class FournisseurCreate(FournisseurBase):
    entreprise_id: str

class FournisseurUpdate(BaseModel):
    nom: Optional[str] = None
    type: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[EmailStr] = None
    adresse: Optional[str] = None
    matricule_fiscal: Optional[str] = None
    delai_livraison: Optional[int] = None

class FournisseurResponse(FournisseurBase):
    id: str
    entreprise_id: str
    score_fiabilite: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================
# PREVISION SCHEMAS (Phase 2)
# ============================================

class PrevisionResponse(BaseModel):
    id: str
    article_id: str
    date_calcul: datetime
    date_periode: datetime
    quantite_prevue: float
    confiance: float
    metriques: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True

# ============================================
# DASHBOARD SCHEMAS
# ============================================

class ArticleFaible(BaseModel):
    id: str
    code: str
    designation: str
    stock_actuel: int
    stock_min: int

class DashboardStats(BaseModel):
    valeur_stock_total_dt: float
    total_articles: int
    articles_faibles_count: int
    articles_rupture_count: int
    articles_faibles: List[ArticleFaible]

# ============================================
# RAPPORT SCHEMAS (Phase 2)
# ============================================

class RapportRequest(BaseModel):
    type: str = Field(..., pattern="^(mouvements|valorisation|marges)$")
    date_debut: datetime
    date_fin: datetime
    magasin_id: str
    format: str = Field(default="pdf", pattern="^(pdf|excel)$")
