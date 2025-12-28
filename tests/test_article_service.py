import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.article_service import ArticleService
from app.core.exceptions import ArticleNotFoundException, InsufficientStockException


@pytest.fixture
def article_service():
    return ArticleService()


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.article = MagicMock()
    return db


@pytest.mark.asyncio
async def test_create_article_success(article_service, mock_db):
    """Test création d'article avec succès"""
    article_data = {
        "code": "ART001",
        "designation": "Test Article",
        "prix_achat": 10.0,
        "prix_vente": 15.0,
        "stock_min": 5,
        "stock_max": 100,
        "stock_actuel": 50
    }
    
    mock_db.article.create = AsyncMock(return_value=MagicMock(**article_data, id="123"))
    
    result = await article_service.create_article(mock_db, "magasin_1", article_data)
    
    assert result.code == "ART001"
    assert result.designation == "Test Article"
    mock_db.article.create.assert_called_once()


@pytest.mark.asyncio
async def test_get_article_by_code_success(article_service, mock_db):
    """Test récupération d'article par code"""
    mock_article = MagicMock(
        id="123",
        code="ART001",
        designation="Test Article",
        stock_actuel=50
    )
    
    mock_db.article.find_first = AsyncMock(return_value=mock_article)
    
    result = await article_service.get_article_by_code(mock_db, "magasin_1", "ART001")
    
    assert result.code == "ART001"
    assert result.stock_actuel == 50


@pytest.mark.asyncio
async def test_get_article_not_found(article_service, mock_db):
    """Test article non trouvé"""
    mock_db.article.find_first = AsyncMock(return_value=None)
    
    with pytest.raises(ArticleNotFoundException):
        await article_service.get_article_by_code(mock_db, "magasin_1", "INVALID")


@pytest.mark.asyncio
async def test_update_stock_success(article_service, mock_db):
    """Test mise à jour du stock"""
    mock_article = MagicMock(id="123", stock_actuel=50)
    mock_db.article.find_unique = AsyncMock(return_value=mock_article)
    mock_db.article.update = AsyncMock(return_value=MagicMock(stock_actuel=60))
    
    result = await article_service.update_stock(mock_db, "123", 10)
    
    assert result.stock_actuel == 60
    mock_db.article.update.assert_called_once()


@pytest.mark.asyncio
async def test_get_articles_faibles(article_service, mock_db):
    """Test récupération des articles à stock faible"""
    mock_articles = [
        MagicMock(code="ART001", stock_actuel=3, stock_min=5),
        MagicMock(code="ART002", stock_actuel=2, stock_min=10)
    ]
    
    mock_db.article.find_many = AsyncMock(return_value=mock_articles)
    
    result = await article_service.get_articles_faibles(mock_db, "magasin_1")
    
    assert len(result) == 2
    assert all(a.stock_actuel <= a.stock_min for a in result)


@pytest.mark.asyncio
async def test_search_articles(article_service, mock_db):
    """Test recherche d'articles"""
    mock_articles = [
        MagicMock(code="ART001", designation="Laptop Dell"),
        MagicMock(code="ART002", designation="Laptop HP")
    ]
    
    mock_db.article.find_many = AsyncMock(return_value=mock_articles)
    
    result = await article_service.search_articles(mock_db, "magasin_1", "laptop")
    
    assert len(result) == 2
    mock_db.article.find_many.assert_called_once()


@pytest.mark.asyncio
async def test_validate_stock_availability_success(article_service, mock_db):
    """Test validation de disponibilité du stock"""
    mock_article = MagicMock(stock_actuel=50)
    mock_db.article.find_unique = AsyncMock(return_value=mock_article)
    
    # Ne devrait pas lever d'exception
    await article_service.validate_stock_availability(mock_db, "123", 30)


@pytest.mark.asyncio
async def test_validate_stock_availability_insufficient(article_service, mock_db):
    """Test stock insuffisant"""
    mock_article = MagicMock(code="ART001", stock_actuel=10)
    mock_db.article.find_unique = AsyncMock(return_value=mock_article)
    
    with pytest.raises(InsufficientStockException):
        await article_service.validate_stock_availability(mock_db, "123", 50)


@pytest.mark.asyncio
async def test_calculate_stock_value(article_service, mock_db):
    """Test calcul de la valeur du stock"""
    mock_articles = [
        MagicMock(stock_actuel=10, prix_achat=100.0, prix_vente=150.0),
        MagicMock(stock_actuel=20, prix_achat=50.0, prix_vente=75.0)
    ]
    
    mock_db.article.find_many = AsyncMock(return_value=mock_articles)
    
    result = await article_service.calculate_stock_value(mock_db, "magasin_1")
    
    assert result["valeur_achat"] == 2000.0  # (10*100) + (20*50)
    assert result["valeur_vente"] == 3000.0  # (10*150) + (20*75)
    assert result["marge"] == 1000.0


@pytest.mark.asyncio
async def test_delete_article_soft_delete(article_service, mock_db):
    """Test suppression logique d'article"""
    mock_article = MagicMock(id="123", is_active=True)
    mock_db.article.find_unique = AsyncMock(return_value=mock_article)
    mock_db.article.update = AsyncMock(return_value=MagicMock(is_active=False))
    
    result = await article_service.delete_article(mock_db, "123")
    
    assert result.is_active == False
    mock_db.article.update.assert_called_once()
