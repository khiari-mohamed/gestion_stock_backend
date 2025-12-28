"""
Production-grade notification service
Supports Email (SendGrid) and WhatsApp (Twilio)
With queueing, retry logic, and delivery tracking
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.core.database import prisma
from app.core.config import settings
import logging
import aiohttp
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"
    IN_APP = "IN_APP"


class NotificationStatus(str, Enum):
    PENDING = "EN_ATTENTE"
    SENT = "ENVOYEE"
    DELIVERED = "LIVREE"
    FAILED = "ECHEC"


class EmailService:
    """SendGrid email service for production"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        self.from_email = getattr(settings, 'FROM_EMAIL', 'no-reply@stockflowpro.com')
        self.max_retries = 3
        self.base_url = "https://api.sendgrid.com/v3/mail/send"
    
    async def send(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> Dict:
        """
        Send email via SendGrid
        
        Returns status dict with:
        - success: bool
        - message_id: str or None
        - error: str or None
        """
        if not self.api_key:
            logger.warning("SendGrid API key not configured - skipping email")
            return {
                "success": False,
                "message_id": None,
                "error": "SendGrid not configured"
            }
        
        payload = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": subject
                }
            ],
            "from": {
                "email": self.from_email,
                "name": "StockFlow Pro"
            },
            "content": [
                {
                    "type": "text/html",
                    "value": html_content
                }
            ]
        }
        
        if text_content:
            payload["content"].append({
                "type": "text/plain",
                "value": text_content
            })
        
        if reply_to:
            payload["reply_to"] = {"email": reply_to}
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    async with session.post(
                        self.base_url,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status in [200, 202]:
                            message_id = response.headers.get("X-Message-Id")
                            logger.info(f"Email sent to {to_email}: {message_id}")
                            return {
                                "success": True,
                                "message_id": message_id,
                                "error": None
                            }
                        else:
                            error_text = await response.text()
                            logger.warning(
                                f"SendGrid error ({response.status}): {error_text}"
                            )
                            
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(2 ** attempt)
                                continue
                            
                            return {
                                "success": False,
                                "message_id": None,
                                "error": f"SendGrid error: {response.status}"
                            }
            
            except asyncio.TimeoutError:
                logger.error(f"Email send timeout (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return {
                    "success": False,
                    "message_id": None,
                    "error": "Request timeout"
                }
            
            except Exception as e:
                logger.error(f"Email send error: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return {
                    "success": False,
                    "message_id": None,
                    "error": str(e)
                }
        
        return {
            "success": False,
            "message_id": None,
            "error": "Max retries exceeded"
        }


class WhatsAppService:
    """Twilio WhatsApp Business API service"""
    
    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.from_number = getattr(settings, 'TWILIO_WHATSAPP_FROM', None)
        self.max_retries = 3
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json" if self.account_sid else None
    
    async def send(
        self,
        to_number: str,
        message: str,
        media_urls: Optional[List[str]] = None
    ) -> Dict:
        """
        Send WhatsApp message via Twilio
        
        Args:
            to_number: Recipient phone in format +216XXXXXXXX
            message: Message text
            media_urls: Optional list of media URLs
        
        Returns status dict
        """
        if not self.account_sid or not self.auth_token:
            logger.warning("Twilio credentials not configured - skipping WhatsApp")
            return {
                "success": False,
                "message_id": None,
                "error": "Twilio not configured"
            }
        
        # Normalize phone number
        to_number = self._normalize_phone(to_number)
        if not to_number:
            return {
                "success": False,
                "message_id": None,
                "error": "Invalid phone number"
            }
        
        payload = {
            "From": f"whatsapp:{self.from_number}",
            "To": f"whatsapp:{to_number}",
            "Body": message
        }
        
        if media_urls:
            payload["MediaUrl"] = media_urls
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)
                    
                    async with session.post(
                        self.base_url,
                        data=payload,
                        auth=auth,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 201:
                            data = await response.json()
                            message_id = data.get("sid")
                            logger.info(f"WhatsApp sent to {to_number}: {message_id}")
                            return {
                                "success": True,
                                "message_id": message_id,
                                "error": None
                            }
                        else:
                            error_text = await response.text()
                            logger.warning(
                                f"Twilio error ({response.status}): {error_text}"
                            )
                            
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(2 ** attempt)
                                continue
                            
                            return {
                                "success": False,
                                "message_id": None,
                                "error": f"Twilio error: {response.status}"
                            }
            
            except Exception as e:
                logger.error(f"WhatsApp send error: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return {
                    "success": False,
                    "message_id": None,
                    "error": str(e)
                }
        
        return {
            "success": False,
            "message_id": None,
            "error": "Max retries exceeded"
        }
    
    def _normalize_phone(self, phone: str) -> Optional[str]:
        """Normalize phone number to Twilio format"""
        import re
        
        if not phone:
            return None
        
        # Remove all non-digits
        digits = re.sub(r"\D", "", phone)
        
        # Handle Tunisia numbers
        if digits.startswith("216"):
            return f"+{digits}"
        elif digits.startswith("2160"):
            return f"+{digits}"
        elif len(digits) == 8 and digits[0] in "2345679":
            return f"+216{digits}"
        
        return None


class NotificationService:
    """Main notification service - orchestrates all channels"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.whatsapp_service = WhatsAppService()
    
    async def send_notification(
        self,
        titre: str,
        message: str,
        canal: str,
        destinaire: str,
        entreprise_id: str,
        alerte_id: Optional[str] = None,
        type_notification: str = "ALERTE"
    ) -> Dict:
        """
        Send notification through specified channel
        
        Stores notification in database for tracking
        """
        notification = None
        
        try:
            # Create notification record
            notification = await prisma.notification.create(
                data={
                    "titre": titre,
                    "message": message,
                    "canal": canal,
                    "type": type_notification,
                    "statut": "EN_ATTENTE",
                    "destinaire": destinaire,
                    "entreprise_id": entreprise_id,
                    "alerte_id": alerte_id
                }
            )
            
            # Send through channel
            result = None
            
            if canal == "EMAIL":
                result = await self.email_service.send(
                    to_email=destinaire,
                    subject=titre,
                    html_content=message
                )
            
            elif canal == "WHATSAPP":
                result = await self.whatsapp_service.send(
                    to_number=destinaire,
                    message=message
                )
            
            elif canal == "IN_APP":
                # In-app notifications are always successful (stored in DB)
                result = {"success": True, "message_id": notification.id, "error": None}
            
            # Update notification status
            if result and result.get("success"):
                await prisma.notification.update(
                    where={"id": notification.id},
                    data={
                        "statut": "ENVOYEE",
                        "date_envoi": datetime.utcnow()
                    }
                )
                
                logger.info(f"Notification sent: {notification.id}")
                
                return {
                    "success": True,
                    "notification_id": notification.id,
                    "message_id": result.get("message_id")
                }
            
            else:
                error_msg = result.get("error") if result else "Unknown error"
                
                await prisma.notification.update(
                    where={"id": notification.id},
                    data={
                        "statut": "ECHEC",
                        "erreur": error_msg
                    }
                )
                
                logger.error(f"Notification failed: {notification.id} - {error_msg}")
                
                return {
                    "success": False,
                    "notification_id": notification.id,
                    "error": error_msg
                }
        
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            
            if notification:
                await prisma.notification.update(
                    where={"id": notification.id},
                    data={
                        "statut": "ECHEC",
                        "erreur": str(e)
                    }
                )
            
            return {
                "success": False,
                "notification_id": notification.id if notification else None,
                "error": str(e)
            }
    
    async def send_stock_alert(
        self,
        article: Dict,
        user_phone: str,
        user_email: str,
        alert_type: str,
        entreprise_id: str,
        canal_config: str = "LES_DEUX",
        alerte_id: Optional[str] = None
    ):
        """Send stock alert via configured channels"""
        
        if alert_type == "RUPTURE":
            titre = f"🚨 RUPTURE DE STOCK: {article['designation']}"
            message = f"Article {article['code']} en rupture de stock\nStock actuel: 0\nSeuil minimum: {article['stock_min']}"
        
        elif alert_type == "SEUIL_BAS":
            titre = f"⚠️ STOCK FAIBLE: {article['designation']}"
            message = f"Stock actuel: {article['stock_actuel']}\nSeuil minimum: {article['stock_min']}"
        
        elif alert_type == "PEREMPTION":
            titre = f"⏰ ALERTE PÉREMPTION: {article['designation']}"
            message = f"Article périme dans {article.get('jours_restants', '?')} jours"
        
        else:
            titre = f"📦 ALERTE STOCK: {article['designation']}"
            message = "Vérifiez votre stock"
        
        # Send via WhatsApp (priority for urgent alerts)
        if user_phone and canal_config in ["WHATSAPP", "LES_DEUX"]:
            await self.send_notification(
                titre=titre,
                message=message,
                canal="WHATSAPP",
                destinaire=user_phone,
                entreprise_id=entreprise_id,
                alerte_id=alerte_id,
                type_notification="ALERTE"
            )
        
        # Also send via Email
        if user_email and canal_config in ["EMAIL", "LES_DEUX"]:
            html_message = f"<h2>{titre}</h2><p>{message.replace(chr(10), '<br>')}</p>"
            
            await self.send_notification(
                titre=titre,
                message=html_message,
                canal="EMAIL",
                destinaire=user_email,
                entreprise_id=entreprise_id,
                alerte_id=alerte_id,
                type_notification="ALERTE"
            )
    
    async def get_pending_notifications(self, limit: int = 100) -> List:
        """Get pending notifications for retry"""
        return await prisma.notification.find_many(
            where={"statut": "EN_ATTENTE"},
            take=limit,
            order={"created_at": "asc"}
        )
    
    async def retry_failed_notifications(self) -> Dict:
        """Retry notifications that failed in last hour"""
        
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        failed = await prisma.notification.find_many(
            where={
                "statut": "ECHEC",
                "created_at": {"gte": one_hour_ago}
            }
        )
        
        success_count = 0
        failure_count = 0
        
        for notification in failed:
            try:
                # Retry sending
                if notification.canal == "EMAIL":
                    result = await self.email_service.send(
                        to_email=notification.destinaire,
                        subject=notification.titre,
                        html_content=notification.message
                    )
                
                elif notification.canal == "WHATSAPP":
                    result = await self.whatsapp_service.send(
                        to_number=notification.destinaire,
                        message=notification.message
                    )
                
                else:
                    continue
                
                if result.get("success"):
                    await prisma.notification.update(
                        where={"id": notification.id},
                        data={
                            "statut": "ENVOYEE",
                            "date_envoi": datetime.utcnow()
                        }
                    )
                    success_count += 1
                else:
                    failure_count += 1
            
            except Exception as e:
                logger.error(f"Error retrying notification {notification.id}: {str(e)}")
                failure_count += 1
        
        logger.info(f"Retry notifications: {success_count} success, {failure_count} failures")
        
        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "total": len(failed)
        }

