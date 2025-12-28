import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from app.services.mouvement_service import MouvementService
from app.core.exceptions import ArticleNotFoundException, InsufficientStockException


@pytest.fixture
def mouvement_service():
    return MouvementService()


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.mouvementstock = MagicMock()
    db.article = MagicMock()
    return db


@pytest.mark.asyncio
async def test_create_mouvement_entree(mouvement_service, mock_db):
    """Test création d'un mouvement d'entrée"""
    mock_article = MagicMock(id="art_1", stock_actuel=50, code="ART001")
    mock_db.article.find_unique = AsyncMock(return_value=mock_article)
    mock_db.article.update = AsyncMock(return_value=MagicMock(stock_actuel=60))
    mock_db.mouvementstock.create = AsyncMock(return_value=MagicMock(
        id="mouv_1",
        type="ENTREE",
        quantite=10
    ))
    
    mouvement_data = {
        "article_id": "art_1",
        "type": "ENTREE",
        "quantite": 10,
        "prix_unitaire": 100.0,
        "motif": "Réapprovisionnement"
    }
    
    result = await mouvement_service.create_mouvement(mock_db, "magasin_1", mouvement_data)
    
    assert result.type == "ENTREE"
    assert result.quantite == 10
    mock_db.article.update.assert_called_once()


@pytest.mark.asyncio
async def test_create_mouvement_sortie_success(mouvement_service, mock_db):
    """Test création d'un mouvement de sortie avec stock suffisant"""
    mock_article = MagicMock(id="art_1", stock_actuel=50, code="ART001")
    mock_db.article.find_unique = AsyncMock(return_value=mock_article)
    mock_db.article.update = AsyncMock(return_value=MagicMock(stock_actuel=40))
    mock_db.mouvementstock.create = AsyncMock(return_value=MagicMock(
        id="mouv_1",
        type="SORTIE",
        quantite=10
    ))
    
    mouvement_data = {
        "article_id": "art_1",
        "type": "SORTIE",
        "quantite": 10,
        "motif": "Vente"
    }
    
    result = await mouvement_service.create_mouvement(mock_db, "magasin_1", mouvement_data)
    
    assert result.type == "SORTIE"
    mock_db.article.update.assert_called_once()


@pytest.mark.asyncio
async def test_create_mouvement_sortie_insufficient_stock(mouvement_service, mock_db):
    """Test mouvement de sortie avec stock insuffisant"""
    mock_article = MagicMock(id="art_1", stock_actuel=5, code="ART001")
    mock_db.article.find_unique = AsyncMock(return_value=mock_article)
    
    mouvement_data = {
        "article_id": "art_1",
        "type": "SORTIE",
        "quantite": 10,
        "motif": "Vente"
    }
    
    with pytest.raises(InsufficientStockException):
        await mouvement_service.create_mouvement(mock_db, "magasin_1", mouvement_data)


@pytest.mark.asyncio
async def test_create_mouvement_ajustement(mouvement_service, mock_db):
    """Test création d'un mouvement d'ajustement"""
    mock_article = MagicMock(id="art_1", stock_actuel=50, code="ART001")
    mock_db.article.find_unique = AsyncMock(return_value=mock_article)
    mock_db.article.update = AsyncMock(return_value=MagicMock(stock_actuel=45))
    mock_db.mouvementstock.create = AsyncMock(return_value=MagicMock(
        id="mouv_1",
        type="AJUSTEMENT",
        quantite=-5
    ))
    
    mouvement_data = {
        "article_id": "art_1",
        "type": "AJUSTEMENT",
        "quantite": -5,
        "motif": "Inventaire - casse"
    }
    
    result = await mouvement_service.create_mouvement(mock_db, "magasin_1", mouvement_data)
    
    assert result.type == "AJUSTEMENT"
    mock_db.article.update.assert_called_once()


@pytest.mark.asyncio
async def test_get_mouvements_by_article(mouvement_service, mock_db):
    """Test récupération des mouvements par article"""
    mock_mouvements = [
        MagicMock(id="1", type="ENTREE", quantite=10),
        MagicMock(id="2", type="SORTIE", quantite=5)
    ]
    
    mock_db.mouvementstock.find_many = AsyncMock(return_value=mock_mouvements)
    
    result = await mouvement_service.get_mouvements_by_article(mock_db, "art_1")
    
    assert len(result) == 2
    mock_db.mouvementstock.find_many.assert_called_once()


@pytest.mark.asyncio
async def test_get_mouvements_by_date_range(mouvement_service, mock_db):
    """Test récupération des mouvements par période"""
    date_debut = datetime(2024, 1, 1)
    date_fin = datetime(2024, 1, 31)
    
    mock_mouvements = [
        MagicMock(id="1", date_mouvement=datetime(2024, 1, 15)),
        MagicMock(id="2", date_mouvement=datetime(2024, 1, 20))
    ]
    
    mock_db.mouvementstock.find_many = AsyncMock(return_value=mock_mouvements)
    
    result = await mouvement_service.get_mouvements_by_date_range(
        mock_db, "magasin_1", date_debut, date_fin
    )
    
    assert len(result) == 2
    mock_db.mouvementstock.find_many.assert_called_once()


@pytest.mark.asyncio
async def test_calculate_valeur_totale(mouvement_service, mock_db):
    """Test calcul de la valeur totale d'un mouvement"""
    mouvement_data = {
        "quantite": 10,
        "prix_unitaire": 100.0
    }
    
    valeur = mouvement_service.calculate_valeur_totale(mouvement_data)
    
    assert valeur == 1000.0


@pytest.mark.asyncio
async def test_get_mouvements_by_type(mouvement_service, mock_db):
    """Test récupération des mouvements par type"""
    mock_mouvements = [
        MagicMock(id="1", type="ENTREE"),
        MagicMock(id="2", type="ENTREE")
    ]
    
    mock_db.mouvementstock.find_many = AsyncMock(return_value=mock_mouvements)
    
    result = await mouvement_service.get_mouvements_by_type(mock_db, "magasin_1", "ENTREE")
    
    assert len(result) == 2
    assert all(m.type == "ENTREE" for m in result)


@pytest.mark.asyncio
async def test_update_stock_on_mouvement_entree(mouvement_service, mock_db):
    """Test mise à jour du stock lors d'une entrée"""
    mock_article = MagicMock(stock_actuel=50)
    mock_db.article.find_unique = AsyncMock(return_value=mock_article)
    mock_db.article.update = AsyncMock(return_value=MagicMock(stock_actuel=60))
    
    await mouvement_service._update_stock(mock_db, "art_1", "ENTREE", 10)
    
    mock_db.article.update.assert_called_once_with(
        where={"id": "art_1"},
        data={"stock_actuel": 60}
    )


@pytest.mark.asyncio
async def test_update_stock_on_mouvement_sortie(mouvement_service, mock_db):
    """Test mise à jour du stock lors d'une sortie"""
    mock_article = MagicMock(stock_actuel=50)
    mock_db.article.find_unique = AsyncMock(return_value=mock_article)
    mock_db.article.update = AsyncMock(return_value=MagicMock(stock_actuel=40))
    
    await mouvement_service._update_stock(mock_db, "art_1", "SORTIE", 10)
    
    mock_db.article.update.assert_called_once_with(
        where={"id": "art_1"},
        data={"stock_actuel": 40}
    )
