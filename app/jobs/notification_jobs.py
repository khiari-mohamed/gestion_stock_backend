"""
Jobs asynchrones pour l'envoi de notifications
"""
from typing import List
from app.core.database import get_db
from app.services.whatsapp_service import WhatsAppService
from app.services.notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)


async def send_whatsapp_alerts(entreprise_id: str, alert_type: str, message: str):
    """Envoyer des alertes WhatsApp aux utilisateurs concernés"""
    db = await get_db()
    whatsapp_service = WhatsAppService()
    
    # Récupérer les utilisateurs PATRON/GERANT avec WhatsApp activé
    users = await db.user.find_many(
        where={
            "entreprise_id": entreprise_id,
            "role": {"in": ["PATRON", "GERANT"]},
            "is_active": True,
            "telephone": {"not": None}
        }
    )
    
    sent_count = 0
    for user in users:
        try:
            success = await whatsapp_service.send_alert(
                phone_number=user.telephone,
                message=message,
                alert_type=alert_type
            )
            
            if success:
                sent_count += 1
                
                # Enregistrer la notification
                await db.notification.create(
                    data={
                        "entreprise_id": entreprise_id,
                        "type": "ALERTE",
                        "titre": f"Alerte {alert_type}",
                        "message": message,
                        "canal": "WHATSAPP",
                        "statut": "ENVOYEE",
                        "destinaire": user.telephone,
                        "date_envoi": datetime.now()
                    }
                )
        
        except Exception as e:
            logger.error(f"Failed to send WhatsApp to {user.email}: {str(e)}")
    
    return sent_count


async def send_email_notifications(entreprise_id: str, subject: str, body: str):
    """Envoyer des notifications par email"""
    db = await get_db()
    notification_service = NotificationService()
    
    users = await db.user.find_many(
        where={
            "entreprise_id": entreprise_id,
            "is_active": True
        }
    )
    
    sent_count = 0
    for user in users:
        try:
            success = await notification_service.send_email(
                to_email=user.email,
                subject=subject,
                body=body
            )
            
            if success:
                sent_count += 1
        
        except Exception as e:
            logger.error(f"Failed to send email to {user.email}: {str(e)}")
    
    return sent_count


async def process_pending_notifications():
    """Traiter les notifications en attente"""
    db = await get_db()
    
    pending = await db.notification.find_many(
        where={"statut": "EN_ATTENTE"},
        take=100
    )
    
    processed = 0
    for notif in pending:
        try:
            if notif.canal == "WHATSAPP":
                whatsapp_service = WhatsAppService()
                success = await whatsapp_service.send_alert(
                    phone_number=notif.destinaire,
                    message=notif.message,
                    alert_type=notif.type
                )
            elif notif.canal == "EMAIL":
                notification_service = NotificationService()
                success = await notification_service.send_email(
                    to_email=notif.destinaire,
                    subject=notif.titre,
                    body=notif.message
                )
            else:
                success = True  # IN_APP notifications
            
            if success:
                await db.notification.update(
                    where={"id": notif.id},
                    data={"statut": "ENVOYEE", "date_envoi": datetime.now()}
                )
                processed += 1
            else:
                await db.notification.update(
                    where={"id": notif.id},
                    data={"statut": "ECHEC", "erreur": "Failed to send"}
                )
        
        except Exception as e:
            logger.error(f"Error processing notification {notif.id}: {str(e)}")
            await db.notification.update(
                where={"id": notif.id},
                data={"statut": "ECHEC", "erreur": str(e)}
            )
    
    return processed
