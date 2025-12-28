import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from app.services.article_service import ArticleService
from app.services.mouvement_service import MouvementService
from app.services.dashboard_service import DashboardService


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.article = MagicMock()
    db.mouvementstock = MagicMock()
    db.vente = MagicMock()
    return db


@pytest.mark.asyncio
async def test_complete_stock_flow(mock_db):
    """Test du flux complet: création article -> entrée stock -> sortie stock -> dashboard"""
    
    article_service = ArticleService()
    mouvement_service = MouvementService()
    dashboard_service = DashboardService()
    
    # 1. Créer un article
    article_data = {
        "code": "ART001",
        "designation": "Laptop Dell",
        "prix_achat": 1000.0,
        "prix_vente": 1500.0,
        "stock_min": 5,
        "stock_max": 50,
        "stock_actuel": 0
    }
    
    mock_article = MagicMock(**article_data, id="art_1")
    mock_db.article.create = AsyncMock(return_value=mock_article)
    
    article = await article_service.create_article(mock_db, "mag_1", article_data)
    assert article.code == "ART001"
    assert article.stock_actuel == 0
    
    # 2. Entrée de stock
    mock_db.article.find_unique = AsyncMock(return_value=mock_article)
    mock_article.stock_actuel = 10
    mock_db.article.update = AsyncMock(return_value=mock_article)
    mock_db.mouvementstock.create = AsyncMock(return_value=MagicMock(
        id="mouv_1",
        type="ENTREE",
        quantite=10
    ))
    
    mouvement_entree = await mouvement_service.create_mouvement(mock_db, "mag_1", {
        "article_id": "art_1",
        "type": "ENTREE",
        "quantite": 10,
        "prix_unitaire": 1000.0,
        "motif": "Réapprovisionnement"
    })
    
    assert mouvement_entree.type == "ENTREE"
    assert mouvement_entree.quantite == 10
    
    # 3. Sortie de stock
    mock_article.stock_actuel = 7
    mock_db.article.update = AsyncMock(return_value=mock_article)
    mock_db.mouvementstock.create = AsyncMock(return_value=MagicMock(
        id="mouv_2",
        type="SORTIE",
        quantite=3
    ))
    
    mouvement_sortie = await mouvement_service.create_mouvement(mock_db, "mag_1", {
        "article_id": "art_1",
        "type": "SORTIE",
        "quantite": 3,
        "motif": "Vente"
    })
    
    assert mouvement_sortie.type == "SORTIE"
    
    # 4. Vérifier le dashboard
    mock_db.article.find_many = AsyncMock(return_value=[mock_article])
    
    stock_value = await dashboard_service.calculate_stock_value(mock_db, "mag_1")
    assert stock_value["valeur_totale_dt"] == 7000.0  # 7 * 1000


@pytest.mark.asyncio
async def test_stock_alert_workflow(mock_db):
    """Test du workflow d'alerte de stock faible"""
    
    article_service = ArticleService()
    dashboard_service = DashboardService()
    
    # Article avec stock faible
    mock_article = MagicMock(
        id="art_1",
        code="ART001",
        designation="Article Test",
        stock_actuel=3,
        stock_min=10,
        prix_achat=100.0
    )
    
    mock_db.article.find_many = AsyncMock(return_value=[mock_article])
    
    # Récupérer les articles faibles
    articles_faibles = await dashboard_service.get_articles_faibles(mock_db, "mag_1")
    
    assert len(articles_faibles) == 1
    assert articles_faibles[0].stock_actuel < articles_faibles[0].stock_min


@pytest.mark.asyncio
async def test_inventory_adjustment_workflow(mock_db):
    """Test du workflow d'ajustement d'inventaire"""
    
    mouvement_service = MouvementService()
    
    # Stock théorique vs stock physique
    mock_article = MagicMock(
        id="art_1",
        code="ART001",
        stock_actuel=50
    )
    
    mock_db.article.find_unique = AsyncMock(return_value=mock_article)
    
    # Inventaire physique: 45 unités (5 de moins)
    stock_physique = 45
    ecart = stock_physique - mock_article.stock_actuel  # -5
    
    mock_article.stock_actuel = 45
    mock_db.article.update = AsyncMock(return_value=mock_article)
    mock_db.mouvementstock.create = AsyncMock(return_value=MagicMock(
        id="mouv_1",
        type="AJUSTEMENT",
        quantite=ecart
    ))
    
    ajustement = await mouvement_service.create_mouvement(mock_db, "mag_1", {
        "article_id": "art_1",
        "type": "AJUSTEMENT",
        "quantite": ecart,
        "motif": "Inventaire - casse"
    })
    
    assert ajustement.type == "AJUSTEMENT"
    assert ajustement.quantite == -5


@pytest.mark.asyncio
async def test_multi_article_purchase_workflow(mock_db):
    """Test du workflow d'achat multiple d'articles"""
    
    mouvement_service = MouvementService()
    
    articles_to_purchase = [
        {"id": "art_1", "code": "ART001", "quantite": 10, "prix": 100.0},
        {"id": "art_2", "code": "ART002", "quantite": 20, "prix": 50.0},
        {"id": "art_3", "code": "ART003", "quantite": 5, "prix": 200.0}
    ]
    
    total_value = 0
    
    for article in articles_to_purchase:
        mock_article = MagicMock(
            id=article["id"],
            code=article["code"],
            stock_actuel=0
        )
        
        mock_db.article.find_unique = AsyncMock(return_value=mock_article)
        mock_article.stock_actuel = article["quantite"]
        mock_db.article.update = AsyncMock(return_value=mock_article)
        mock_db.mouvementstock.create = AsyncMock(return_value=MagicMock(
            type="ENTREE",
            quantite=article["quantite"],
            prix_unitaire=article["prix"]
        ))
        
        mouvement = await mouvement_service.create_mouvement(mock_db, "mag_1", {
            "article_id": article["id"],
            "type": "ENTREE",
            "quantite": article["quantite"],
            "prix_unitaire": article["prix"],
            "motif": "Bon de commande BC001"
        })
        
        total_value += article["quantite"] * article["prix"]
    
    # Valeur totale de l'achat
    expected_total = (10 * 100) + (20 * 50) + (5 * 200)  # 3000
    assert total_value == expected_total


@pytest.mark.asyncio
async def test_stock_valuation_with_tva(mock_db):
    """Test du workflow de valorisation du stock avec TVA"""
    
    dashboard_service = DashboardService()
    
    mock_articles = [
        MagicMock(
            stock_actuel=10,
            prix_achat=100.0,
            tva_taux=0.19
        ),
        MagicMock(
            stock_actuel=20,
            prix_achat=50.0,
            tva_taux=0.19
        )
    ]
    
    mock_db.article.find_many = AsyncMock(return_value=mock_articles)
    
    result = await dashboard_service.calculate_stock_value_with_tva(mock_db, "mag_1")
    
    valeur_ht = (10 * 100) + (20 * 50)  # 2000
    tva = valeur_ht * 0.19  # 380
    valeur_ttc = valeur_ht + tva  # 2380
    
    assert result["valeur_ht"] == valeur_ht
    assert result["tva"] == tva
    assert result["valeur_ttc"] == valeur_ttc


@pytest.mark.asyncio
async def test_return_workflow(mock_db):
    """Test du workflow de retour fournisseur"""
    
    mouvement_service = MouvementService()
    
    # Article défectueux à retourner
    mock_article = MagicMock(
        id="art_1",
        code="ART001",
        stock_actuel=50
    )
    
    mock_db.article.find_unique = AsyncMock(return_value=mock_article)
    mock_article.stock_actuel = 45
    mock_db.article.update = AsyncMock(return_value=mock_article)
    mock_db.mouvementstock.create = AsyncMock(return_value=MagicMock(
        id="mouv_1",
        type="RETOUR",
        quantite=5
    ))
    
    retour = await mouvement_service.create_mouvement(mock_db, "mag_1", {
        "article_id": "art_1",
        "type": "RETOUR",
        "quantite": 5,
        "motif": "Produits défectueux",
        "fournisseur_id": "fourn_1"
    })
    
    assert retour.type == "RETOUR"
    assert retour.quantite == 5
