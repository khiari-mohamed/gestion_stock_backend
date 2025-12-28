"""
Advanced Analytics Service - Production Grade
Calculates: cash immobilized, TVA reporting, stock rotation, trend analysis
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.core.database import prisma
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class AdvancedAnalyticsService:
    """Production-grade analytics engine"""
    
    @staticmethod
    async def get_financial_dashboard(
        magasin_id: str,
        date_debut: Optional[datetime] = None,
        date_fin: Optional[datetime] = None
    ) -> Dict:
        """
        Get comprehensive financial dashboard
        Includes: cash immobilized, TVA, margins, turnover
        """
        try:
            # Default date range: last 30 days
            if not date_debut:
                date_fin = datetime.now()
                date_debut = date_fin - timedelta(days=30)
            elif not date_fin:
                date_fin = datetime.now()
            
            warehouse = await prisma.magasin.find_unique(
                where={"id": magasin_id},
                include={"articles": True}
            )
            
            if not warehouse:
                return {"error": "Magasin non trouvé"}
            
            # Get all sales for period
            ventes = await prisma.vente.find_many(
                where={
                    "magasin_id": magasin_id,
                    "date_vente": {"gte": date_debut, "lte": date_fin}
                },
                include={"article": True}
            )
            
            # Financial Metrics
            dashboard = {
                "period": {
                    "debut": date_debut.isoformat(),
                    "fin": date_fin.isoformat(),
                    "jours": (date_fin - date_debut).days
                },
                "cash_immobilized": await AdvancedAnalyticsService._calculate_cash_immobilized(magasin_id),
                "tva_report": await AdvancedAnalyticsService._calculate_tva(ventes),
                "margins": await AdvancedAnalyticsService._calculate_margins(ventes),
                "stock_rotation": await AdvancedAnalyticsService._calculate_stock_rotation(ventes, warehouse.articles),
                "sales_performance": await AdvancedAnalyticsService._analyze_sales_performance(ventes, date_debut, date_fin),
                "inventory_health": await AdvancedAnalyticsService._analyze_inventory_health(magasin_id, warehouse.articles)
            }
            
            return dashboard
        
        except Exception as e:
            logger.error(f"Error getting financial dashboard: {e}")
            return {"error": str(e)}
    
    @staticmethod
    async def _calculate_cash_immobilized(magasin_id: str) -> Dict:
        """
        Calculate cash immobilized in inventory
        Formula: Σ(stock_current * prix_achat)
        Risk value: Σ(stock_current * prix_vente)
        """
        try:
            articles = await prisma.article.find_many(
                where={"magasin_id": magasin_id}
            )
            
            cash_immobilized = 0.0
            risk_value = 0.0
            total_articles = 0
            
            for article in articles:
                if article.stock_actuel > 0:
                    # Cost value = current stock * purchase price
                    cash_immobilized += article.stock_actuel * article.prix_achat
                    # Risk value = current stock * sale price
                    risk_value += article.stock_actuel * article.prix_vente
                    total_articles += 1
            
            # Calculate average day to sell (DTS)
            # DTS = stock_average / (monthly_sales / 30)
            last_30_ventes = await prisma.vente.find_many(
                where={
                    "magasin_id": magasin_id,
                    "date_vente": {"gte": datetime.now() - timedelta(days=30)}
                }
            )
            
            avg_daily_sales = len(last_30_ventes) / 30 if last_30_ventes else 0
            days_to_sell = (cash_immobilized / risk_value * 100) if risk_value > 0 else 0
            
            # Excess inventory = amount above 45 days of stock
            excess_threshold = avg_daily_sales * 45 * (sum(a.prix_achat for a in articles if a.stock_actuel > 0) / len([a for a in articles if a.stock_actuel > 0]) if any(a.stock_actuel > 0 for a in articles) else 0)
            excess_cash = max(0, cash_immobilized - excess_threshold)
            
            return {
                "cash_immobilized_total": round(cash_immobilized, 2),
                "risk_value": round(risk_value, 2),
                "articles_in_stock": total_articles,
                "average_article_value": round(cash_immobilized / total_articles, 2) if total_articles > 0 else 0,
                "days_to_sell": round(days_to_sell, 1),
                "excess_inventory_value": round(excess_cash, 2),
                "efficiency_ratio": round((risk_value - cash_immobilized) / risk_value * 100, 2) if risk_value > 0 else 0
            }
        
        except Exception as e:
            logger.error(f"Error calculating cash immobilized: {e}")
            return {}
    
    @staticmethod
    async def _calculate_tva(ventes: List) -> Dict:
        """
        Calculate TVA report
        Breaks down: HT (without tax), TVA amount, TTC (with tax)
        TVA rates: 19% (standard), 7% (reduced), 0% (exempt)
        """
        try:
            total_ht = 0.0
            total_tva = 0.0
            total_ttc = 0.0
            tva_by_rate = {19: 0.0, 7: 0.0, 0: 0.0}
            
            for vente in ventes:
                # Calculate HT (before tax)
                prix_ht = vente.prix_unitaire / (1 + (vente.article.taux_tva or 0.19) / 100)
                montant_ht = prix_ht * vente.quantite
                
                # Calculate TVA
                taux_tva = vente.article.taux_tva or 19
                montant_tva = montant_ht * (taux_tva / 100)
                montant_ttc = montant_ht + montant_tva
                
                total_ht += montant_ht
                total_tva += montant_tva
                total_ttc += montant_ttc
                
                if taux_tva in tva_by_rate:
                    tva_by_rate[taux_tva] += montant_tva
            
            return {
                "total_ht": round(total_ht, 2),
                "total_tva": round(total_tva, 2),
                "total_ttc": round(total_ttc, 2),
                "tva_detail": {
                    "rate_19": round(tva_by_rate[19], 2),
                    "rate_7": round(tva_by_rate[7], 2),
                    "rate_0": round(tva_by_rate[0], 2)
                },
                "effective_tva_rate": round((total_tva / total_ht * 100), 2) if total_ht > 0 else 0
            }
        
        except Exception as e:
            logger.error(f"Error calculating TVA: {e}")
            return {}
    
    @staticmethod
    async def _calculate_margins(ventes: List) -> Dict:
        """
        Calculate profit margins
        Gross margin = (sale_price - purchase_price) / sale_price * 100
        """
        try:
            if not ventes:
                return {}
            
            total_revenue = 0.0
            total_cost = 0.0
            margins = []
            
            for vente in ventes:
                prix_vente_total = vente.prix_unitaire * vente.quantite
                prix_achat_total = vente.article.prix_achat * vente.quantite
                
                total_revenue += prix_vente_total
                total_cost += prix_achat_total
                
                if vente.prix_unitaire > 0:
                    margin = ((vente.prix_unitaire - vente.article.prix_achat) / vente.prix_unitaire) * 100
                    margins.append(margin)
            
            gross_margin = ((total_revenue - total_cost) / total_revenue * 100) if total_revenue > 0 else 0
            
            return {
                "gross_margin_percent": round(gross_margin, 2),
                "total_revenue": round(total_revenue, 2),
                "total_cost": round(total_cost, 2),
                "total_profit": round(total_revenue - total_cost, 2),
                "average_margin": round(np.mean(margins), 2) if margins else 0,
                "margin_range": {
                    "min": round(min(margins), 2) if margins else 0,
                    "max": round(max(margins), 2) if margins else 0,
                    "std_dev": round(np.std(margins), 2) if margins else 0
                }
            }
        
        except Exception as e:
            logger.error(f"Error calculating margins: {e}")
            return {}
    
    @staticmethod
    async def _calculate_stock_rotation(ventes: List, articles: List) -> Dict:
        """
        Calculate stock rotation metrics
        Rotation rate = annual_sales / average_inventory
        Days of inventory = 365 / rotation_rate
        """
        try:
            if not ventes or not articles:
                return {}
            
            # Calculate annual sales per article
            annual_sales_by_article = {}
            for vente in ventes:
                article_id = vente.article_id
                if article_id not in annual_sales_by_article:
                    annual_sales_by_article[article_id] = 0
                annual_sales_by_article[article_id] += vente.quantite
            
            # Calculate rotation for each article
            rotations = []
            inventory_values = []
            
            for article in articles:
                if article.id in annual_sales_by_article:
                    annual_quantity = annual_sales_by_article[article.id] * 12 / (len(ventes) / 30 if ventes else 1)
                    
                    if article.stock_actuel > 0:
                        rotation_rate = annual_quantity / article.stock_actuel
                        rotations.append(rotation_rate)
                    
                    inventory_value = article.stock_actuel * article.prix_achat
                    inventory_values.append(inventory_value)
            
            avg_rotation = np.mean(rotations) if rotations else 0
            total_inventory = sum(inventory_values)
            
            return {
                "average_rotation_rate": round(avg_rotation, 2),
                "days_of_inventory": round(365 / avg_rotation, 1) if avg_rotation > 0 else 0,
                "total_inventory_value": round(total_inventory, 2),
                "articles_analyzed": len(rotations),
                "fast_movers": len([r for r in rotations if r > avg_rotation * 1.5]) if rotations else 0,
                "slow_movers": len([r for r in rotations if r < avg_rotation * 0.5]) if rotations else 0
            }
        
        except Exception as e:
            logger.error(f"Error calculating stock rotation: {e}")
            return {}
    
    @staticmethod
    async def _analyze_sales_performance(ventes: List, date_debut: datetime, date_fin: datetime) -> Dict:
        """
        Analyze sales trends and performance
        """
        try:
            if not ventes:
                return {}
            
            # Group by date
            df = pd.DataFrame([{
                "date": v.date_vente,
                "quantite": v.quantite,
                "prix": v.prix_unitaire,
                "montant": v.prix_unitaire * v.quantite
            } for v in ventes])
            
            daily_sales = df.groupby('date').agg({
                'montant': 'sum',
                'quantite': 'sum'
            }).reset_index()
            
            if daily_sales.empty:
                return {}
            
            montants = daily_sales['montant'].values
            
            # Calculate growth trend
            if len(montants) > 1:
                trend = "croissant" if montants[-1] > montants[0] else "décroissant"
                growth = ((montants[-1] - montants[0]) / montants[0] * 100) if montants[0] > 0 else 0
            else:
                trend = "stable"
                growth = 0
            
            return {
                "total_sales_quantity": int(df['quantite'].sum()),
                "total_sales_revenue": round(df['montant'].sum(), 2),
                "average_daily_sales": round(np.mean(montants), 2),
                "max_daily_sales": round(np.max(montants), 2),
                "min_daily_sales": round(np.min(montants), 2),
                "std_deviation": round(np.std(montants), 2),
                "trend": trend,
                "growth_percent": round(growth, 2),
                "days_with_sales": len(daily_sales),
                "average_transaction_value": round(df['montant'].sum() / len(df), 2)
            }
        
        except Exception as e:
            logger.error(f"Error analyzing sales performance: {e}")
            return {}
    
    @staticmethod
    async def _analyze_inventory_health(magasin_id: str, articles: List) -> Dict:
        """
        Analyze inventory health
        Identifies: overstocked, understocked, obsolete
        """
        try:
            if not articles:
                return {}
            
            overstocked = 0
            understocked = 0
            optimal = 0
            obsolete = 0
            
            total_value = 0
            critical_value = 0
            
            for article in articles:
                article_value = article.stock_actuel * article.prix_achat
                total_value += article_value
                
                # Classification
                if article.stock_actuel == 0:
                    obsolete += 1
                elif article.stock_actuel > article.stock_max:
                    overstocked += 1
                    critical_value += article_value
                elif article.stock_actuel < article.stock_min:
                    understocked += 1
                    critical_value += article_value
                else:
                    optimal += 1
            
            health_score = (optimal / len(articles) * 100) if articles else 0
            
            return {
                "total_articles": len(articles),
                "optimal_stock": optimal,
                "overstocked": overstocked,
                "understocked": understocked,
                "obsolete": obsolete,
                "health_score_percent": round(health_score, 2),
                "total_inventory_value": round(total_value, 2),
                "at_risk_value": round(critical_value, 2),
                "status": "Excellent" if health_score > 80 else "Bon" if health_score > 60 else "À améliorer"
            }
        
        except Exception as e:
            logger.error(f"Error analyzing inventory health: {e}")
            return {}
    
    @staticmethod
    async def get_top_products(
        magasin_id: str,
        limit: int = 10,
        metric: str = "revenue"
    ) -> List[Dict]:
        """
        Get top performing products
        Metrics: revenue, quantity, margin, rotation
        """
        try:
            ventes = await prisma.vente.find_many(
                where={"magasin_id": magasin_id},
                include={"article": True},
                take=limit * 5
            )
            
            if not ventes:
                return []
            
            # Aggregate by article
            article_metrics = {}
            
            for vente in ventes:
                article_id = vente.article_id
                if article_id not in article_metrics:
                    article_metrics[article_id] = {
                        "id": article_id,
                        "code": vente.article.code,
                        "designation": vente.article.designation,
                        "total_quantity": 0,
                        "total_revenue": 0,
                        "total_cost": 0,
                        "transactions": 0
                    }
                
                article_metrics[article_id]["total_quantity"] += vente.quantite
                article_metrics[article_id]["total_revenue"] += vente.prix_unitaire * vente.quantite
                article_metrics[article_id]["total_cost"] += vente.article.prix_achat * vente.quantite
                article_metrics[article_id]["transactions"] += 1
            
            # Add calculated fields
            for article_id, metrics in article_metrics.items():
                metrics["profit"] = metrics["total_revenue"] - metrics["total_cost"]
                metrics["margin_percent"] = (metrics["profit"] / metrics["total_revenue"] * 100) if metrics["total_revenue"] > 0 else 0
                metrics["avg_transaction"] = metrics["total_revenue"] / metrics["transactions"]
            
            # Sort by metric
            if metric == "revenue":
                sorted_products = sorted(
                    article_metrics.values(),
                    key=lambda x: x["total_revenue"],
                    reverse=True
                )
            elif metric == "quantity":
                sorted_products = sorted(
                    article_metrics.values(),
                    key=lambda x: x["total_quantity"],
                    reverse=True
                )
            elif metric == "margin":
                sorted_products = sorted(
                    article_metrics.values(),
                    key=lambda x: x["margin_percent"],
                    reverse=True
                )
            else:
                sorted_products = sorted(
                    article_metrics.values(),
                    key=lambda x: x["total_revenue"],
                    reverse=True
                )
            
            return [
                {
                    "rank": i + 1,
                    **{k: v for k, v in product.items()}
                }
                for i, product in enumerate(sorted_products[:limit])
            ]
        
        except Exception as e:
            logger.error(f"Error getting top products: {e}")
            return []
