from datetime import datetime, timedelta
from typing import List, Dict

def calculate_stock_value(articles: List[Dict]) -> float:
    """
    Calculer la valeur totale du stock
    """
    return sum(a.get("stock_actuel", 0) * a.get("prix_achat", 0) for a in articles)

def calculate_marge(prix_achat: float, prix_vente: float) -> float:
    """
    Calculer la marge en pourcentage
    """
    if prix_achat == 0:
        return 0
    return ((prix_vente - prix_achat) / prix_achat) * 100

def get_week_range(date: datetime = None) -> tuple:
    """
    Obtenir le début et la fin de la semaine
    """
    if not date:
        date = datetime.now()
    
    start = date - timedelta(days=date.weekday())
    end = start + timedelta(days=6)
    
    return start, end

def format_currency_dt(amount: float) -> str:
    """
    Formater un montant en dinars tunisiens
    """
    return f"{amount:.3f} DT"

def is_jour_ferie(date: datetime, jours_feries: List[datetime]) -> bool:
    """
    Vérifier si une date est un jour férié
    """
    return date.date() in [j.date() for j in jours_feries]

def calculate_taux_rotation(ventes_periode: float, stock_moyen: float) -> float:
    """
    Calculer le taux de rotation du stock
    """
    if stock_moyen == 0:
        return 0
    return ventes_periode / stock_moyen
