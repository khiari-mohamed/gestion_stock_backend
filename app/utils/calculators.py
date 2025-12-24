"""
Utilitaires de calcul pour la gestion de stock
"""
from typing import Dict, List


def calculate_stock_value(articles: List) -> Dict:
    """Calculer la valeur totale du stock"""
    valeur_achat = sum(a.stock_actuel * a.prix_achat for a in articles)
    valeur_vente = sum(a.stock_actuel * a.prix_vente for a in articles)
    
    return {
        "valeur_achat_ht": round(valeur_achat, 3),
        "valeur_vente_ht": round(valeur_vente, 3),
        "marge_brute": round(valeur_vente - valeur_achat, 3),
        "taux_marge": round(((valeur_vente - valeur_achat) / valeur_achat * 100) if valeur_achat > 0 else 0, 2)
    }


def calculate_tva(montant_ht: float, taux_tva: float = 0.19) -> Dict:
    """Calculer la TVA tunisienne"""
    tva = montant_ht * taux_tva
    montant_ttc = montant_ht + tva
    
    return {
        "montant_ht": round(montant_ht, 3),
        "tva": round(tva, 3),
        "montant_ttc": round(montant_ttc, 3),
        "taux_tva": taux_tva
    }


def calculate_margin(prix_achat: float, prix_vente: float) -> Dict:
    """Calculer les marges"""
    marge_brute = prix_vente - prix_achat
    taux_marge = (marge_brute / prix_achat * 100) if prix_achat > 0 else 0
    taux_marque = (marge_brute / prix_vente * 100) if prix_vente > 0 else 0
    
    return {
        "marge_brute": round(marge_brute, 3),
        "taux_marge": round(taux_marge, 2),
        "taux_marque": round(taux_marque, 2)
    }


def calculate_rotation_stock(ventes_annuelles: float, stock_moyen: float) -> float:
    """Calculer le taux de rotation du stock"""
    if stock_moyen == 0:
        return 0
    return round(ventes_annuelles / stock_moyen, 2)


def calculate_couverture_stock(stock_actuel: int, ventes_moyennes_jour: float) -> int:
    """Calculer la couverture du stock en jours"""
    if ventes_moyennes_jour == 0:
        return 999
    return int(stock_actuel / ventes_moyennes_jour)


def convert_currency(montant: float, devise_source: str, devise_cible: str) -> float:
    """Convertir entre devises (taux fixes pour MVP)"""
    taux = {
        ("TND", "EUR"): 0.30,
        ("TND", "USD"): 0.32,
        ("EUR", "TND"): 3.33,
        ("USD", "TND"): 3.13,
        ("EUR", "USD"): 1.07,
        ("USD", "EUR"): 0.93
    }
    
    if devise_source == devise_cible:
        return montant
    
    taux_conversion = taux.get((devise_source, devise_cible), 1.0)
    return round(montant * taux_conversion, 2)


def calculate_economic_order_quantity(
    demande_annuelle: float,
    cout_commande: float,
    cout_stockage: float
) -> int:
    """Calculer la quantité économique de commande (EOQ)"""
    import math
    
    if cout_stockage == 0:
        return 0
    
    eoq = math.sqrt((2 * demande_annuelle * cout_commande) / cout_stockage)
    return int(eoq)
