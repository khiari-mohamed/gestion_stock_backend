import pytest
from pydantic import ValidationError
from app.schemas.article import ArticleCreate, ArticleUpdate
from app.schemas.mouvement import MouvementStockCreate

def test_article_create_valid():
    """Test de création d'un article valide"""
    data = {
        "code": "TEST001",
        "designation": "Article Test",
        "prix_achat": 10.0,
        "prix_vente": 15.0,
        "stock_min": 5,
        "stock_max": 50,
        "magasin_id": "magasin-123"
    }
    article = ArticleCreate(**data)
    assert article.code == "TEST001"
    assert article.prix_achat == 10.0

def test_article_create_invalid_prix():
    """Test de validation des prix négatifs"""
    with pytest.raises(ValidationError):
        ArticleCreate(
            code="TEST001",
            designation="Article Test",
            prix_achat=-10.0,
            prix_vente=15.0,
            magasin_id="magasin-123"
        )

def test_mouvement_stock_valid():
    """Test de création d'un mouvement valide"""
    data = {
        "type": "entree",
        "quantite": 50,
        "prix_unitaire": 10.0,
        "article_id": "article-123",
        "magasin_id": "magasin-123"
    }
    mouvement = MouvementStockCreate(**data)
    assert mouvement.type == "entree"
    assert mouvement.quantite == 50

def test_mouvement_stock_invalid_type():
    """Test de validation du type de mouvement"""
    with pytest.raises(ValidationError):
        MouvementStockCreate(
            type="invalid_type",
            quantite=50,
            article_id="article-123",
            magasin_id="magasin-123"
        )

def test_mouvement_stock_invalid_quantite():
    """Test de validation de la quantité (doit être > 0)"""
    with pytest.raises(ValidationError):
        MouvementStockCreate(
            type="entree",
            quantite=0,
            article_id="article-123",
            magasin_id="magasin-123"
        )
