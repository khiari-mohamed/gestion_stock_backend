"""
Advanced AI forecasting service with multiple algorithms
Supports: Moving Average (V1.0), Facebook Prophet (V1.5), Ensemble models (V2.0)
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
from app.core.database import prisma
import numpy as np
import pandas as pd
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ForecastAlgorithm(str, Enum):
    MOVING_AVERAGE = "moving_average"  # V1.0 MVP
    PROPHET = "prophet"  # V1.5 Advanced
    ENSEMBLE = "ensemble"  # V2.0 Production


class AIForecastServiceV2:
    """Production-grade AI forecasting service"""
    
    def __init__(self):
        self.version_modele = "2.0"
        self.algorithms = {
            ForecastAlgorithm.MOVING_AVERAGE: self._forecast_moving_average,
            ForecastAlgorithm.PROPHET: self._forecast_prophet,
            ForecastAlgorithm.ENSEMBLE: self._forecast_ensemble,
        }
    
    async def generate_forecast(
        self,
        article_id: str,
        magasin_id: str,
        horizon_jours: int = 7,
        algorithm: ForecastAlgorithm = ForecastAlgorithm.MOVING_AVERAGE
    ) -> Optional[Dict]:
        """
        Generate demand forecast for article
        
        Supports multiple algorithms with automatic fallback
        """
        try:
            # Fetch sales history
            date_debut = datetime.now() - timedelta(weeks=12)  # 3 months
            
            ventes = await prisma.vente.find_many(
                where={
                    "article_id": article_id,
                    "magasin_id": magasin_id,
                    "date_vente": {"gte": date_debut}
                },
                order={"date_vente": "asc"}
            )
            
            if len(ventes) < 4:
                logger.warning(f"Insufficient data for {article_id}: {len(ventes)} sales")
                return None
            
            # Convert to pandas for easier manipulation
            df_ventes = pd.DataFrame([
                {
                    "date": v.date_vente,
                    "quantite": v.quantite,
                    "semaine": v.semaine_annee
                }
                for v in ventes
            ])
            
            # Get forecast based on algorithm
            forecast_result = None
            
            if algorithm == ForecastAlgorithm.MOVING_AVERAGE:
                forecast_result = await self._forecast_moving_average(
                    df_ventes, article_id, magasin_id, horizon_jours
                )
            
            elif algorithm == ForecastAlgorithm.PROPHET:
                # Try Prophet, fall back to moving average if unavailable
                try:
                    forecast_result = await self._forecast_prophet(
                        df_ventes, article_id, magasin_id, horizon_jours
                    )
                except Exception as e:
                    logger.warning(f"Prophet failed for {article_id}, falling back: {e}")
                    forecast_result = await self._forecast_moving_average(
                        df_ventes, article_id, magasin_id, horizon_jours
                    )
            
            elif algorithm == ForecastAlgorithm.ENSEMBLE:
                try:
                    forecast_result = await self._forecast_ensemble(
                        df_ventes, article_id, magasin_id, horizon_jours
                    )
                except Exception as e:
                    logger.warning(f"Ensemble failed for {article_id}: {e}")
                    return None
            
            if not forecast_result:
                return None
            
            # Save to database
            date_periode = datetime.now() + timedelta(days=1)
            date_fin_periode = date_periode + timedelta(days=horizon_jours)
            
            prevision = await prisma.prevision.upsert(
                where={
                    "article_id_magasin_id_date_periode": {
                        "article_id": article_id,
                        "magasin_id": magasin_id,
                        "date_periode": date_periode
                    }
                },
                data={
                    "create": {
                        "article_id": article_id,
                        "magasin_id": magasin_id,
                        "date_periode": date_periode,
                        "date_fin_periode": date_fin_periode,
                        "quantite_prevue": round(forecast_result["quantite_prevue"], 2),
                        "confiance": round(forecast_result["confiance"], 2),
                        "algorithme": algorithm.value,
                        "version_modele": self.version_modele,
                        "metriques": forecast_result.get("metriques")
                    },
                    "update": {
                        "quantite_prevue": round(forecast_result["quantite_prevue"], 2),
                        "confiance": round(forecast_result["confiance"], 2),
                        "metriques": forecast_result.get("metriques"),
                        "date_calcul": datetime.now(),
                        "algorithme": algorithm.value,
                        "version_modele": self.version_modele
                    }
                }
            )
            
            logger.info(f"Forecast generated for {article_id} using {algorithm.value}")
            
            return {
                "article_id": article_id,
                "quantite_prevue": round(forecast_result["quantite_prevue"], 2),
                "confiance": round(forecast_result["confiance"], 2),
                "algorithme": algorithm.value,
                "metriques": forecast_result.get("metriques"),
                "horizon_jours": horizon_jours
            }
        
        except Exception as e:
            logger.error(f"Error generating forecast for {article_id}: {str(e)}")
            return None
    
    async def _forecast_moving_average(
        self,
        df: pd.DataFrame,
        article_id: str,
        magasin_id: str,
        horizon: int
    ) -> Dict:
        """
        Simple weighted moving average forecast (V1.0)
        Fast, reliable, works with limited data
        """
        try:
            quantites = df['quantite'].values.astype(float)
            
            # Weighted average: more recent sales are weighted higher
            weights = np.linspace(0.5, 1.0, len(quantites))
            quantite_prevue = np.average(quantites, weights=weights)
            
            # Confidence based on variance
            variance = np.var(quantites)
            std_dev = np.std(quantites)
            
            # Confidence = inverse of coefficient of variation
            if quantite_prevue > 0:
                cv = std_dev / quantite_prevue
                confiance = max(0.3, min(0.95, 1.0 / (1.0 + cv)))
            else:
                confiance = 0.3
            
            # Metrics
            metriques = self._calculate_metrics(quantites, quantite_prevue)
            
            return {
                "quantite_prevue": quantite_prevue,
                "confiance": confiance,
                "metriques": metriques,
                "algoritm": "moving_average"
            }
        
        except Exception as e:
            logger.error(f"Moving average error: {e}")
            return None
    
    async def _forecast_prophet(
        self,
        df: pd.DataFrame,
        article_id: str,
        magasin_id: str,
        horizon: int
    ) -> Optional[Dict]:
        """
        Facebook Prophet forecast (V1.5)
        Handles seasonality, trends, and holidays
        """
        try:
            from fbprophet import Prophet
            
            # Prepare data for Prophet
            df_prophet = df[['date', 'quantite']].copy()
            df_prophet.columns = ['ds', 'y']
            df_prophet = df_prophet.drop_duplicates(subset=['ds'])
            df_prophet = df_prophet.sort_values('ds')
            
            if len(df_prophet) < 14:  # Prophet needs at least 2 weeks
                return None
            
            # Fit model
            model = Prophet(
                yearly_seasonality=len(df_prophet) > 365,
                weekly_seasonality=True,
                daily_seasonality=False,
                interval_width=0.95,
                changepoint_prior_scale=0.05
            )
            
            model.fit(df_prophet)
            
            # Make forecast
            future = model.make_future_dataframe(periods=horizon)
            forecast = model.predict(future)
            
            # Get next period forecast
            next_forecast = forecast[forecast['ds'] > df_prophet['ds'].max()].iloc[0]
            
            quantite_prevue = max(0, next_forecast['yhat'])
            
            # Confiance basée sur l'intervalle de confiance
            yhat_lower = max(0, next_forecast['yhat_lower'])
            yhat_upper = next_forecast['yhat_upper']
            
            # Narrower interval = higher confidence
            interval_width = yhat_upper - yhat_lower
            confiance = max(0.3, min(0.95, 1.0 / (1.0 + interval_width / quantite_prevue) if quantite_prevue > 0 else 0.3))
            
            # Metrics
            metriques = self._calculate_metrics(
                df_prophet['y'].values,
                quantite_prevue
            )
            metriques["method"] = "prophet"
            metriques["trend"] = str(next_forecast.get('trend', 'stable'))
            
            return {
                "quantite_prevue": quantite_prevue,
                "confiance": confiance,
                "metriques": metriques,
                "algoritm": "prophet"
            }
        
        except ImportError:
            logger.warning("Prophet not installed, falling back to moving average")
            return None
        
        except Exception as e:
            logger.error(f"Prophet error: {e}")
            return None
    
    async def _forecast_ensemble(
        self,
        df: pd.DataFrame,
        article_id: str,
        magasin_id: str,
        horizon: int
    ) -> Optional[Dict]:
        """
        Ensemble forecast combining multiple algorithms (V2.0)
        Weighted average of moving average and prophet
        """
        try:
            # Get both forecasts
            ma_forecast = await self._forecast_moving_average(df, article_id, magasin_id, horizon)
            prophet_forecast = await self._forecast_prophet(df, article_id, magasin_id, horizon)
            
            if not ma_forecast:
                return prophet_forecast
            
            if not prophet_forecast:
                return ma_forecast
            
            # Weight forecasts by confidence
            ma_conf = ma_forecast["confiance"]
            prop_conf = prophet_forecast["confiance"]
            total_conf = ma_conf + prop_conf
            
            # Weighted average
            quantite_prevue = (
                ma_forecast["quantite_prevue"] * (ma_conf / total_conf) +
                prophet_forecast["quantite_prevue"] * (prop_conf / total_conf)
            )
            
            # Average confidence
            confiance = (ma_conf + prop_conf) / 2
            
            # Combined metrics
            metriques = {
                "ensemble_method": "weighted_average",
                "moving_average_weight": round(ma_conf / total_conf, 2),
                "prophet_weight": round(prop_conf / total_conf, 2),
                "combined_confidence": round(confiance, 2),
                "ma_prediction": round(ma_forecast["quantite_prevue"], 2),
                "prophet_prediction": round(prophet_forecast["quantite_prevue"], 2)
            }
            
            return {
                "quantite_prevue": quantite_prevue,
                "confiance": confiance,
                "metriques": metriques,
                "algoritm": "ensemble"
            }
        
        except Exception as e:
            logger.error(f"Ensemble error: {e}")
            return None
    
    def _calculate_metrics(self, historique: np.ndarray, prevision: float) -> Dict:
        """Calculate forecast accuracy metrics"""
        try:
            # MAPE (Mean Absolute Percentage Error)
            mape_values = [abs((h - prevision) / h) for h in historique if h > 0]
            mape = np.mean(mape_values) * 100 if mape_values else 0
            
            # WMAPE (Weighted MAPE)
            total_actual = np.sum(historique)
            total_error = np.sum([abs(h - prevision) for h in historique])
            wmape = (total_error / total_actual * 100) if total_actual > 0 else 0
            
            # Coverage
            coverage = (len(historique) / 28) * 100  # 28 days = 4 weeks
            
            # MAE (Mean Absolute Error)
            mae = np.mean([abs(h - prevision) for h in historique])
            
            return {
                "mape": round(mape, 2),
                "wmape": round(wmape, 2),
                "mae": round(mae, 2),
                "coverage": round(min(coverage, 100), 2),
                "data_points": len(historique)
            }
        
        except Exception as e:
            logger.error(f"Metrics calculation error: {e}")
            return {}
    
    async def get_purchase_suggestions(self, magasin_id: str) -> List[Dict]:
        """Generate purchase recommendations"""
        try:
            # Get recent forecasts
            date_limite = datetime.now() - timedelta(days=1)
            
            previsions = await prisma.prevision.find_many(
                where={
                    "magasin_id": magasin_id,
                    "date_calcul": {"gte": date_limite}
                },
                include={"article": True}
            )
            
            suggestions = []
            
            for prev in previsions:
                article = prev.article
                stock_actuel = article.stock_actuel
                demande_prevue = prev.quantite_prevue
                stock_securite = article.stock_securite
                
                # Quantity needed = forecast + safety stock - current stock
                quantite_necessaire = demande_prevue + stock_securite - stock_actuel
                
                if quantite_necessaire > 0:
                    # Determine priority
                    if stock_actuel <= article.stock_min:
                        priorite = "CRITIQUE"
                        urgence = 1
                    elif stock_actuel <= (article.stock_min + article.stock_securite):
                        priorite = "HAUTE"
                        urgence = 2
                    else:
                        priorite = "NORMALE"
                        urgence = 3
                    
                    suggestions.append({
                        "article_id": article.id,
                        "code": article.code,
                        "designation": article.designation,
                        "stock_actuel": stock_actuel,
                        "stock_min": article.stock_min,
                        "stock_securite": stock_securite,
                        "demande_prevue": round(demande_prevue, 0),
                        "quantite_a_commander": round(max(article.stock_min, quantite_necessaire), 0),
                        "confiance": round(prev.confiance, 2),
                        "priorite": priorite,
                        "urgence": urgence,
                        "cout_estime": round(round(quantite_necessaire, 0) * article.prix_achat, 2),
                        "valeur_risque_rupture": round(article.stock_actuel * article.prix_vente, 2)
                    })
            
            # Sort by urgency and value risk
            suggestions.sort(key=lambda x: (x["urgence"], -x["valeur_risque_rupture"]))
            
            return suggestions
        
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return []
    
    async def analyze_forecast_accuracy(self, article_id: str, magasin_id: str) -> Dict:
        """Analyze forecast accuracy for continuous improvement"""
        try:
            # Compare old forecasts with actual sales
            month_ago = datetime.now() - timedelta(days=30)
            
            previsions = await prisma.prevision.find_many(
                where={
                    "article_id": article_id,
                    "magasin_id": magasin_id,
                    "date_calcul": {"gte": month_ago}
                }
            )
            
            if not previsions:
                return {"message": "No forecasts to analyze"}
            
            # Get actual sales for same periods
            ventes = await prisma.vente.find_many(
                where={
                    "article_id": article_id,
                    "magasin_id": magasin_id,
                    "date_vente": {"gte": month_ago}
                }
            )
            
            # Calculate accuracy metrics
            if len(ventes) > 0 and len(previsions) > 0:
                avg_prevision = np.mean([p.quantite_prevue for p in previsions])
                avg_vente = np.mean([v.quantite for v in ventes])
                
                accuracy = 100 - abs((avg_prevision - avg_vente) / avg_vente * 100) if avg_vente > 0 else 0
                
                return {
                    "article_id": article_id,
                    "periode": "30 jours",
                    "previsions_count": len(previsions),
                    "ventes_count": len(ventes),
                    "prevision_moyenne": round(avg_prevision, 2),
                    "vente_moyenne": round(avg_vente, 2),
                    "accuracy_percent": round(max(0, min(100, accuracy)), 2),
                    "analyse": "Excellent" if accuracy > 85 else "Bon" if accuracy > 70 else "À améliorer"
                }
            
            return {"message": "Insufficient data"}
        
        except Exception as e:
            logger.error(f"Forecast analysis error: {e}")
            return {"error": str(e)}
