"""
Advanced Alert System - Production Grade
Features: Deduplication, escalation, complex conditions, batch sending
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.core.database import prisma
from app.services.notification_service import NotificationService
import logging
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertType(str, Enum):
    LOW_STOCK = "LOW_STOCK"
    EXPIRATION_SOON = "EXPIRATION_SOON"
    OVERSTOCK = "OVERSTOCK"
    PRICE_CHANGE = "PRICE_CHANGE"
    SUPPLIER_ISSUE = "SUPPLIER_ISSUE"
    FORECAST_ALERT = "FORECAST_ALERT"
    SYSTEM_ALERT = "SYSTEM_ALERT"


class AdvancedAlertSystem:
    """Production-grade alert management"""
    
    @staticmethod
    def _generate_alert_signature(alert_data: Dict) -> str:
        """
        Generate unique signature for alert deduplication
        Uses: article_id + magasin_id + alert_type + date
        """
        signature_parts = [
            alert_data.get("article_id", ""),
            alert_data.get("magasin_id", ""),
            alert_data.get("type"),
            datetime.now().strftime("%Y-%m-%d")
        ]
        signature_str = "|".join(str(p) for p in signature_parts)
        return hashlib.md5(signature_str.encode()).hexdigest()
    
    @staticmethod
    async def create_alert(
        article_id: str,
        magasin_id: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        titre: str,
        description: str,
        metadata: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Create alert with deduplication
        """
        try:
            alert_signature = AdvancedAlertSystem._generate_alert_signature({
                "article_id": article_id,
                "magasin_id": magasin_id,
                "type": alert_type
            })
            
            # Check if similar alert exists (within last 24 hours)
            existing_alert = await prisma.alerte.find_first(
                where={
                    "article_id": article_id,
                    "magasin_id": magasin_id,
                    "type": alert_type.value,
                    "date_creation": {"gte": datetime.now() - timedelta(hours=24)}
                }
            )
            
            if existing_alert:
                # Increment occurrence count instead of creating duplicate
                updated = await prisma.alerte.update(
                    where={"id": existing_alert.id},
                    data={
                        "nombre_occurrences": existing_alert.nombre_occurrences + 1,
                        "date_derniere_occurrence": datetime.now()
                    }
                )
                logger.info(f"Alert deduplicated: {alert_signature}")
                return None  # Don't send duplicate notification
            
            # Create new alert
            alert = await prisma.alerte.create(
                data={
                    "article_id": article_id,
                    "magasin_id": magasin_id,
                    "type": alert_type.value,
                    "severity": severity.value,
                    "titre": titre,
                    "description": description,
                    "signature": alert_signature,
                    "nombre_occurrences": 1,
                    "date_creation": datetime.now(),
                    "date_derniere_occurrence": datetime.now(),
                    "statut": "ACTIF",
                    "metadata": metadata
                }
            )
            
            logger.info(
                f"Alert created: {alert.id} type={alert_type} severity={severity}"
            )
            
            return alert
        
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return None
    
    @staticmethod
    async def check_low_stock_alerts(magasin_id: str) -> List[Dict]:
        """
        Check for low stock and create alerts
        """
        try:
            articles = await prisma.article.find_many(
                where={"magasin_id": magasin_id}
            )
            
            alerts_created = []
            
            for article in articles:
                # Determine severity based on stock level
                if article.stock_actuel <= 0:
                    severity = AlertSeverity.CRITICAL
                    titre = f"RUPTURE DE STOCK: {article.designation}"
                    description = f"L'article {article.code} est en rupture de stock (stock actuel: 0)"
                
                elif article.stock_actuel < article.stock_min:
                    severity = AlertSeverity.CRITICAL
                    titre = f"STOCK CRITIQUE: {article.designation}"
                    description = f"Stock de {article.code} ({article.stock_actuel}) inférieur au minimum ({article.stock_min})"
                
                elif article.stock_actuel < (article.stock_min + article.stock_securite):
                    severity = AlertSeverity.WARNING
                    titre = f"Stock faible: {article.designation}"
                    description = f"Stock de {article.code} ({article.stock_actuel}) approche du minimum"
                
                else:
                    continue
                
                alert = await AdvancedAlertSystem.create_alert(
                    article_id=article.id,
                    magasin_id=magasin_id,
                    alert_type=AlertType.LOW_STOCK,
                    severity=severity,
                    titre=titre,
                    description=description,
                    metadata={
                        "stock_actuel": article.stock_actuel,
                        "stock_min": article.stock_min,
                        "stock_securite": article.stock_securite
                    }
                )
                
                if alert:
                    alerts_created.append(alert)
            
            return alerts_created
        
        except Exception as e:
            logger.error(f"Error checking low stock: {e}")
            return []
    
    @staticmethod
    async def check_expiration_alerts(magasin_id: str) -> List[Dict]:
        """
        Check for items nearing expiration
        """
        try:
            # Get articles expiring within 30 days
            articles_expiring = await prisma.article.find_many(
                where={
                    "magasin_id": magasin_id,
                    "date_peremption": {
                        "gte": datetime.now(),
                        "lte": datetime.now() + timedelta(days=30)
                    }
                }
            )
            
            alerts_created = []
            
            for article in articles_expiring:
                days_until_expiry = (article.date_peremption - datetime.now()).days
                
                if days_until_expiry <= 0:
                    severity = AlertSeverity.CRITICAL
                    titre = f"PRODUIT EXPIRÉ: {article.designation}"
                elif days_until_expiry <= 7:
                    severity = AlertSeverity.CRITICAL
                    titre = f"EXPIRATION IMMINENTE: {article.designation}"
                else:
                    severity = AlertSeverity.WARNING
                    titre = f"Expiration proche: {article.designation}"
                
                description = f"{article.code} expire dans {days_until_expiry} jours (le {article.date_peremption.strftime('%d/%m/%Y')})"
                
                alert = await AdvancedAlertSystem.create_alert(
                    article_id=article.id,
                    magasin_id=magasin_id,
                    alert_type=AlertType.EXPIRATION_SOON,
                    severity=severity,
                    titre=titre,
                    description=description,
                    metadata={
                        "date_peremption": article.date_peremption.isoformat(),
                        "jours_avant_expiration": days_until_expiry
                    }
                )
                
                if alert:
                    alerts_created.append(alert)
            
            return alerts_created
        
        except Exception as e:
            logger.error(f"Error checking expiration: {e}")
            return []
    
    @staticmethod
    async def check_overstock_alerts(magasin_id: str) -> List[Dict]:
        """
        Check for overstocked items
        """
        try:
            articles = await prisma.article.find_many(
                where={
                    "magasin_id": magasin_id,
                    "stock_actuel": {"gt": None}
                }
            )
            
            alerts_created = []
            
            for article in articles:
                if article.stock_actuel > article.stock_max:
                    excess = article.stock_actuel - article.stock_max
                    excess_value = excess * article.prix_achat
                    
                    severity = AlertSeverity.WARNING
                    titre = f"SURSTOCK: {article.designation}"
                    description = (
                        f"{article.code} en surstock: {article.stock_actuel} "
                        f"(max: {article.stock_max}). Excédent: {excess} unités "
                        f"(valeur: {excess_value:.2f} TND)"
                    )
                    
                    alert = await AdvancedAlertSystem.create_alert(
                        article_id=article.id,
                        magasin_id=magasin_id,
                        alert_type=AlertType.OVERSTOCK,
                        severity=severity,
                        titre=titre,
                        description=description,
                        metadata={
                            "stock_actuel": article.stock_actuel,
                            "stock_max": article.stock_max,
                            "quantite_exces": excess,
                            "valeur_exces": excess_value
                        }
                    )
                    
                    if alert:
                        alerts_created.append(alert)
            
            return alerts_created
        
        except Exception as e:
            logger.error(f"Error checking overstock: {e}")
            return []
    
    @staticmethod
    async def escalate_critical_alerts() -> List[Dict]:
        """
        Escalate critical alerts if not resolved within 24 hours
        Sends notification to manager
        """
        try:
            # Find active critical alerts created more than 24 hours ago
            escalation_threshold = datetime.now() - timedelta(hours=24)
            
            critical_alerts = await prisma.alerte.find_many(
                where={
                    "severity": AlertSeverity.CRITICAL.value,
                    "statut": "ACTIF",
                    "date_creation": {"lt": escalation_threshold}
                }
            )
            
            escalated = []
            
            for alert in critical_alerts:
                # Update alert status
                updated_alert = await prisma.alerte.update(
                    where={"id": alert.id},
                    data={"escalation_level": (alert.escalation_level or 0) + 1}
                )
                
                # Get magasin and gerant details
                magasin = await prisma.magasin.find_unique(
                    where={"id": alert.magasin_id},
                    include={"gerant": True}
                )
                
                if magasin and magasin.gerant:
                    # Send escalation notification
                    notification_title = f"ALERTE ESCALADÉE: {alert.titre}"
                    notification_message = (
                        f"{alert.description}\n\n"
                        f"Cette alerte a été créée il y a {alert.nombre_occurrences} heures. "
                        f"Veuillez prendre action immédiatement."
                    )
                    
                    await NotificationService.send_notification(
                        utilisateur_id=magasin.gerant.id,
                        titre=notification_title,
                        contenu=notification_message,
                        type_notification="ESCALATION",
                        canal_preferé="EMAIL"
                    )
                
                escalated.append(updated_alert)
            
            logger.info(f"Escalated {len(escalated)} critical alerts")
            return escalated
        
        except Exception as e:
            logger.error(f"Error escalating alerts: {e}")
            return []
    
    @staticmethod
    async def batch_alert_notifications(magasin_id: str) -> Dict:
        """
        Send batched alerts to warehouse manager
        Groups alerts by severity and type
        """
        try:
            # Get all active alerts for warehouse
            alerts = await prisma.alerte.find_many(
                where={
                    "magasin_id": magasin_id,
                    "statut": "ACTIF",
                    "date_derniere_occurrence": {"gte": datetime.now() - timedelta(hours=1)}
                }
            )
            
            if not alerts:
                return {"message": "Aucune alerte"}
            
            # Group by severity
            alerts_by_severity = {}
            for alert in alerts:
                severity = alert.severity
                if severity not in alerts_by_severity:
                    alerts_by_severity[severity] = []
                alerts_by_severity[severity].append(alert)
            
            # Get warehouse info
            magasin = await prisma.magasin.find_unique(
                where={"id": magasin_id},
                include={"gerant": True}
            )
            
            if not magasin or not magasin.gerant:
                return {"error": "Magasin non trouvé"}
            
            # Build summary
            critical_count = len(alerts_by_severity.get("CRITICAL", []))
            warning_count = len(alerts_by_severity.get("WARNING", []))
            info_count = len(alerts_by_severity.get("INFO", []))
            
            summary = f"""
RÉSUMÉ DES ALERTES - {magasin.nom}
================================================

🔴 CRITIQUES: {critical_count}
🟡 AVERTISSEMENTS: {warning_count}
🔵 INFORMATIONS: {info_count}

DÉTAILS:
"""
            
            for severity, severity_alerts in sorted(alerts_by_severity.items()):
                summary += f"\n{severity}:\n"
                for alert in severity_alerts:
                    summary += f"  - {alert.titre}\n"
            
            # Send batched notification
            await NotificationService.send_notification(
                utilisateur_id=magasin.gerant.id,
                titre=f"Résumé des alertes - {magasin.nom}",
                contenu=summary,
                type_notification="BATCH_ALERT",
                canal_preferé="EMAIL"
            )
            
            logger.info(
                f"Batch alert sent: magasin={magasin_id} "
                f"critical={critical_count} warning={warning_count}"
            )
            
            return {
                "magasin_id": magasin_id,
                "total_alerts": len(alerts),
                "critical": critical_count,
                "warning": warning_count,
                "info": info_count
            }
        
        except Exception as e:
            logger.error(f"Error sending batch alerts: {e}")
            return {"error": str(e)}
    
    @staticmethod
    async def resolve_alert(alert_id: str, resolution_notes: str = "") -> Optional[Dict]:
        """
        Mark alert as resolved
        """
        try:
            alert = await prisma.alerte.update(
                where={"id": alert_id},
                data={
                    "statut": "RÉSOLU",
                    "date_resolution": datetime.now(),
                    "notes_resolution": resolution_notes
                }
            )
            
            logger.info(f"Alert resolved: {alert_id}")
            return alert
        
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return None
    
    @staticmethod
    async def get_alert_dashboard(magasin_id: str) -> Dict:
        """
        Get comprehensive alert dashboard
        """
        try:
            alerts = await prisma.alerte.find_many(
                where={"magasin_id": magasin_id}
            )
            
            active_alerts = [a for a in alerts if a.statut == "ACTIF"]
            resolved_alerts = [a for a in alerts if a.statut == "RÉSOLU"]
            
            # Group by type
            by_type = {}
            for alert in active_alerts:
                alert_type = alert.type
                if alert_type not in by_type:
                    by_type[alert_type] = 0
                by_type[alert_type] += 1
            
            # Group by severity
            by_severity = {}
            for alert in active_alerts:
                severity = alert.severity
                if severity not in by_severity:
                    by_severity[severity] = 0
                by_severity[severity] += 1
            
            return {
                "magasin_id": magasin_id,
                "total_active": len(active_alerts),
                "total_resolved": len(resolved_alerts),
                "by_type": by_type,
                "by_severity": by_severity,
                "resolution_rate": round(
                    len(resolved_alerts) / len(alerts) * 100, 2
                ) if alerts else 0
            }
        
        except Exception as e:
            logger.error(f"Error getting alert dashboard: {e}")
            return {"error": str(e)}
