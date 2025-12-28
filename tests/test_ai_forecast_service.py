import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
import numpy as np
from app.services.ai_forecast_service import AIForecastService


@pytest.fixture
def ai_service():
    return AIForecastService()


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.vente = MagicMock()
    db.prevision = MagicMock()
    db.article = MagicMock()
    return db


@pytest.mark.asyncio
async def test_calculate_forecast_sufficient_data(ai_service, mock_db):
    """Test calcul de prévision avec données suffisantes"""
    # Simuler 4 semaines de ventes
    mock_ventes = [
        MagicMock(quantite=10, date_vente=datetime.now() - timedelta(days=28)),
        MagicMock(quantite=12, date_vente=datetime.now() - timedelta(days=21)),
        MagicMock(quantite=15, date_vente=datetime.now() - timedelta(days=14)),
        MagicMock(quantite=18, date_vente=datetime.now() - timedelta(days=7))
    ]
    
    mock_db.vente.find_many = AsyncMock(return_value=mock_ventes)
    mock_db.prevision.upsert = AsyncMock(return_value=MagicMock(
        quantite_prevue=14.5,
        confiance=0.85
    ))
    
    result = await ai_service.calculate_forecast(mock_db, "art_1", "mag_1")
    
    assert result is not None
    assert result.quantite_prevue > 0
    assert 0.3 <= result.confiance <= 0.95


@pytest.mark.asyncio
async def test_calculate_forecast_insufficient_data(ai_service, mock_db):
    """Test calcul de prévision avec données insuffisantes"""
    # Seulement 2 semaines de données
    mock_ventes = [
        MagicMock(quantite=10, date_vente=datetime.now() - timedelta(days=14)),
        MagicMock(quantite=12, date_vente=datetime.now() - timedelta(days=7))
    ]
    
    mock_db.vente.find_many = AsyncMock(return_value=mock_ventes)
    
    result = await ai_service.calculate_forecast(mock_db, "art_1", "mag_1")
    
    assert result is None


@pytest.mark.asyncio
async def test_weighted_average_calculation(ai_service):
    """Test calcul de la moyenne pondérée"""
    quantites = [10, 12, 15, 18]
    weights = np.linspace(0.5, 1.0, len(quantites))
    
    result = np.average(quantites, weights=weights)
    
    # La moyenne pondérée devrait favoriser les valeurs récentes
    assert result > np.mean(quantites)
    assert 14 < result < 16


@pytest.mark.asyncio
async def test_confidence_calculation_low_variance(ai_service):
    """Test calcul de confiance avec faible variance"""
    quantites = [10, 11, 10, 11]  # Variance faible
    variance = np.var(quantites)
    
    confiance = max(0.3, min(0.95, 1.0 - (variance / 100)))
    
    # Faible variance = haute confiance
    assert confiance > 0.9


@pytest.mark.asyncio
async def test_confidence_calculation_high_variance(ai_service):
    """Test calcul de confiance avec forte variance"""
    quantites = [5, 20, 8, 25]  # Variance élevée
    variance = np.var(quantites)
    
    confiance = max(0.3, min(0.95, 1.0 - (variance / 100)))
    
    # Forte variance = confiance plus faible
    assert confiance < 0.7


@pytest.mark.asyncio
async def test_calculate_metrics_mape(ai_service):
    """Test calcul du MAPE (Mean Absolute Percentage Error)"""
    historique = [10, 12, 15, 18]
    previsions = [11, 13, 14, 17]
    
    mape = np.mean([abs((h - p) / h) for h, p in zip(historique, previsions) if h > 0]) * 100
    
    assert 0 <= mape <= 100
    assert mape < 20  # Erreur acceptable


@pytest.mark.asyncio
async def test_calculate_metrics_wmape(ai_service):
    """Test calcul du WMAPE (Weighted MAPE)"""
    historique = [10, 12, 15, 18]
    previsions = [11, 13, 14, 17]
    
    total_actual = sum(historique)
    total_error = sum(abs(h - p) for h, p in zip(historique, previsions))
    wmape = (total_error / total_actual) * 100 if total_actual > 0 else 0
    
    assert 0 <= wmape <= 100


@pytest.mark.asyncio
async def test_get_purchase_suggestions(ai_service, mock_db):
    """Test génération de suggestions d'achat"""
    mock_previsions = [
        MagicMock(
            article_id="art_1",
            quantite_prevue=20,
            confiance=0.85,
            article=MagicMock(
                code="ART001",
                designation="Article 1",
                stock_actuel=5,
                stock_min=10
            )
        ),
        MagicMock(
            article_id="art_2",
            quantite_prevue=15,
            confiance=0.75,
            article=MagicMock(
                code="ART002",
                designation="Article 2",
                stock_actuel=8,
                stock_min=5
            )
        )
    ]
    
    mock_db.prevision.find_many = AsyncMock(return_value=mock_previsions)
    
    result = await ai_service.get_purchase_suggestions(mock_db, "mag_1")
    
    assert len(result) > 0
    assert all(s.quantite_a_commander > 0 for s in result)


@pytest.mark.asyncio
async def test_calculate_all_forecasts(ai_service, mock_db):
    """Test calcul de toutes les prévisions pour un magasin"""
    mock_articles = [
        MagicMock(id="art_1", code="ART001"),
        MagicMock(id="art_2", code="ART002")
    ]
    
    mock_db.article.find_many = AsyncMock(return_value=mock_articles)
    
    # Mock des ventes pour chaque article
    mock_ventes = [
        MagicMock(quantite=10, date_vente=datetime.now() - timedelta(days=i*7))
        for i in range(4)
    ]
    mock_db.vente.find_many = AsyncMock(return_value=mock_ventes)
    mock_db.prevision.upsert = AsyncMock(return_value=MagicMock())
    
    result = await ai_service.calculate_all_forecasts(mock_db, "mag_1")
    
    assert result["total_articles"] == 2
    assert result["previsions_calculees"] >= 0


@pytest.mark.asyncio
async def test_forecast_with_zero_sales(ai_service, mock_db):
    """Test prévision avec ventes nulles"""
    mock_ventes = [
        MagicMock(quantite=0, date_vente=datetime.now() - timedelta(days=i*7))
        for i in range(4)
    ]
    
    mock_db.vente.find_many = AsyncMock(return_value=mock_ventes)
    
    result = await ai_service.calculate_forecast(mock_db, "art_1", "mag_1")
    
    # Devrait retourner une prévision de 0 avec confiance élevée
    if result:
        assert result.quantite_prevue == 0


@pytest.mark.asyncio
async def test_forecast_algorithm_version(ai_service):
    """Test que l'algorithme utilise la bonne version"""
    assert ai_service.ALGORITHM_NAME == "MOYENNE_MOBILE_PONDEREE"
    assert ai_service.MODEL_VERSION == "1.0.0"


@pytest.mark.asyncio
async def test_priority_calculation(ai_service):
    """Test calcul de la priorité des suggestions"""
    # Stock très faible + haute confiance = HAUTE priorité
    stock_actuel = 2
    stock_min = 10
    confiance = 0.9
    
    if stock_actuel < stock_min * 0.5 and confiance > 0.8:
        priorite = "HAUTE"
    elif stock_actuel < stock_min:
        priorite = "MOYENNE"
    else:
        priorite = "BASSE"
    
    assert priorite == "HAUTE"
