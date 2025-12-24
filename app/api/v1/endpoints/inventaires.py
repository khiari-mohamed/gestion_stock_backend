from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from datetime import datetime

router = APIRouter(prefix="/inventaires", tags=["Inventaires"])


@router.post("/magasin/{magasin_id}/demarrer")
async def demarrer_inventaire(
    magasin_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Démarrer un inventaire physique"""
    articles = await db.article.find_many(
        where={"magasin_id": magasin_id, "is_active": True},
        select={"id": True, "code": True, "designation": True, "stock_actuel": True}
    )
    
    return {
        "magasin_id": magasin_id,
        "date_debut": datetime.now(),
        "articles": articles,
        "total_articles": len(articles)
    }


@router.post("/ajustement")
async def ajuster_stock(
    article_id: str,
    magasin_id: str,
    quantite_comptee: int,
    motif: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Ajuster le stock après comptage physique"""
    article = await db.article.find_unique(
        where={"id": article_id}
    )
    
    if not article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    
    ecart = quantite_comptee - article.stock_actuel
    
    # Créer mouvement d'ajustement
    await db.mouvementstock.create(
        data={
            "type": "AJUSTEMENT",
            "article_id": article_id,
            "magasin_id": magasin_id,
            "quantite": abs(ecart),
            "motif": f"Inventaire physique: {motif}",
            "created_by": current_user.id
        }
    )
    
    # Mettre à jour le stock
    updated_article = await db.article.update(
        where={"id": article_id},
        data={"stock_actuel": quantite_comptee}
    )
    
    return {
        "article_id": article_id,
        "stock_avant": article.stock_actuel,
        "stock_apres": quantite_comptee,
        "ecart": ecart,
        "type_ecart": "surplus" if ecart > 0 else "manquant"
    }


@router.get("/magasin/{magasin_id}/rapport")
async def rapport_inventaire(
    magasin_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Générer un rapport d'inventaire"""
    articles = await db.article.find_many(
        where={"magasin_id": magasin_id, "is_active": True}
    )
    
    valeur_totale = sum(a.stock_actuel * a.prix_achat for a in articles)
    articles_faibles = [a for a in articles if a.stock_actuel <= a.stock_min]
    
    return {
        "magasin_id": magasin_id,
        "date_rapport": datetime.now(),
        "total_articles": len(articles),
        "valeur_stock_total": round(valeur_totale, 2),
        "articles_en_alerte": len(articles_faibles),
        "articles_faibles": articles_faibles
    }
