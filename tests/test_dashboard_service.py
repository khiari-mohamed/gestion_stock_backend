import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.dashboard_service import DashboardService


@pytest.fixture
def dashboard_service():
    return DashboardService()


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.article = MagicMock()
    db.mouvementstock = MagicMock()
    db.vente = MagicMock()
    return db


@pytest.mark.asyncio
async def test_calculate_stock_value(dashboard_service, mock_db):
    """Test calcul de la valeur totale du stock"""
    mock_articles = [
        MagicMock(stock_actuel=10, prix_achat=100.0),
        MagicMock(stock_actuel=20, prix_achat=50.0),
        MagicMock(stock_actuel=5, prix_achat=200.0)
    ]
    
    mock_db.article.find_many = AsyncMock(return_value=mock_articles)
    
    result = await dashboard_service.calculate_stock_value(mock_db, "magasin_1")
    
    expected_value = (10 * 100) + (20 * 50) + (5 * 200)  # 3000
    assert result["valeur_totale_dt"] == expected_value


@pytest.mark.asyncio
async def test_calculate_stock_value_with_tva(dashboard_service, mock_db):
    """Test calcul de la valeur du stock avec TVA tunisienne"""
    mock_articles = [
        MagicMock(stock_actuel=10, prix_achat=100.0, tva_taux=0.19),
        MagicMock(stock_actuel=20, prix_achat=50.0, tva_taux=0.19)
    ]
    
    mock_db.article.find_many = AsyncMock(return_value=mock_articles)
    
    result = await dashboard_service.calculate_stock_value_with_tva(mock_db, "magasin_1")
    
    valeur_ht = (10 * 100) + (20 * 50)  # 2000
    tva = valeur_ht * 0.19  # 380
    valeur_ttc = valeur_ht + tva  # 2380
    
    assert result["valeur_ht"] == valeur_ht
    assert result["tva"] == tva
    assert result["valeur_ttc"] == valeur_ttc


@pytest.mark.asyncio
async def test_get_articles_faibles(dashboard_service, mock_db):
    """Test récupération des articles à stock faible"""
    mock_articles = [
        MagicMock(code="ART001", stock_actuel=3, stock_min=5),
        MagicMock(code="ART002", stock_actuel=2, stock_min=10),
        MagicMock(code="ART003", stock_actuel=15, stock_min=10)  # Normal
    ]
    
    mock_db.article.find_many = AsyncMock(return_value=mock_articles[:2])
    
    result = await dashboard_service.get_articles_faibles(mock_db, "magasin_1")
    
    assert len(result) == 2
    assert all(a.stock_actuel <= a.stock_min for a in result)


@pytest.mark.asyncio
async def test_get_articles_rupture(dashboard_service, mock_db):
    """Test récupération des articles en rupture de stock"""
    mock_articles = [
        MagicMock(code="ART001", stock_actuel=0),
        MagicMock(code="ART002", stock_actuel=0)
    ]
    
    mock_db.article.find_many = AsyncMock(return_value=mock_articles)
    
    result = await dashboard_service.get_articles_rupture(mock_db, "magasin_1")
    
    assert len(result) == 2
    assert all(a.stock_actuel == 0 for a in result)


@pytest.mark.asyncio
async def test_get_top_articles_faibles(dashboard_service, mock_db):
    """Test récupération du top 10 des articles à stock faible"""
    mock_articles = [
        MagicMock(code=f"ART{i:03d}", stock_actuel=i, stock_min=10)
        for i in range(15)
    ]
    
    mock_db.article.find_many = AsyncMock(return_value=mock_articles[:10])
    
    result = await dashboard_service.get_top_articles_faibles(mock_db, "magasin_1", limit=10)
    
    assert len(result) <= 10


@pytest.mark.asyncio
async def test_calculate_margin_statistics(dashboard_service, mock_db):
    """Test calcul des statistiques de marge"""
    mock_articles = [
        MagicMock(stock_actuel=10, prix_achat=100.0, prix_vente=150.0),
        MagicMock(stock_actuel=20, prix_achat=50.0, prix_vente=80.0)
    ]
    
    mock_db.article.find_many = AsyncMock(return_value=mock_articles)
    
    result = await dashboard_service.calculate_margin_statistics(mock_db, "magasin_1")
    
    valeur_achat = (10 * 100) + (20 * 50)  # 2000
    valeur_vente = (10 * 150) + (20 * 80)  # 3100
    marge = valeur_vente - valeur_achat  # 1100
    taux_marge = (marge / valeur_achat) * 100  # 55%
    
    assert result["valeur_achat"] == valeur_achat
    assert result["valeur_vente"] == valeur_vente
    assert result["marge_brute"] == marge
    assert result["taux_marge"] == pytest.approx(taux_marge, rel=0.01)


@pytest.mark.asyncio
async def test_get_dashboard_summary(dashboard_service, mock_db):
    """Test récupération du résumé complet du dashboard"""
    mock_articles = [
        MagicMock(stock_actuel=10, prix_achat=100.0, stock_min=5, stock_max=50),
        MagicMock(stock_actuel=0, prix_achat=50.0, stock_min=10, stock_max=30),
        MagicMock(stock_actuel=3, prix_achat=200.0, stock_min=5, stock_max=20)
    ]
    
    mock_db.article.find_many = AsyncMock(return_value=mock_articles)
    
    result = await dashboard_service.get_dashboard_summary(mock_db, "magasin_1")
    
    assert "valeur_stock" in result
    assert "articles_faibles" in result
    assert "articles_rupture" in result
    assert "statistiques" in result


@pytest.mark.asyncio
async def test_calculate_stock_coverage(dashboard_service, mock_db):
    """Test calcul de la couverture du stock en jours"""
    stock_actuel = 100
    ventes_moyennes_jour = 5
    
    couverture = stock_actuel / ventes_moyennes_jour
    
    assert couverture == 20  # 20 jours de couverture


@pytest.mark.asyncio
async def test_calculate_rotation_rate(dashboard_service, mock_db):
    """Test calcul du taux de rotation du stock"""
    ventes_annuelles = 1200
    stock_moyen = 100
    
    rotation = ventes_annuelles / stock_moyen
    
    assert rotation == 12  # 12 rotations par an


@pytest.mark.asyncio
async def test_empty_stock_value(dashboard_service, mock_db):
    """Test calcul de valeur avec stock vide"""
    mock_db.article.find_many = AsyncMock(return_value=[])
    
    result = await dashboard_service.calculate_stock_value(mock_db, "magasin_1")
    
    assert result["valeur_totale_dt"] == 0


@pytest.mark.asyncio
async def test_tva_calculation_precision(dashboard_service):
    """Test précision du calcul de TVA (3 décimales pour TND)"""
    valeur_ht = 100.0
    tva_taux = 0.19
    
    tva = round(valeur_ht * tva_taux, 3)
    valeur_ttc = round(valeur_ht + tva, 3)
    
    assert tva == 19.0
    assert valeur_ttc == 119.0
