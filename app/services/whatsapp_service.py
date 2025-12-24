import httpx
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service pour envoyer des notifications via WhatsApp Business API"""
    
    def __init__(self):
        self.api_url = getattr(settings, 'WHATSAPP_API_URL', None)
        self.api_token = getattr(settings, 'WHATSAPP_API_TOKEN', None)
        self.enabled = bool(self.api_url and self.api_token)
    
    async def send_alert(
        self,
        phone_number: str,
        message: str,
        alert_type: str = "INFO"
    ) -> bool:
        """
        Envoyer une alerte WhatsApp
        
        Args:
            phone_number: Numéro au format international (+216...)
            message: Contenu du message
            alert_type: Type d'alerte (RUPTURE, PEREMPTION, etc.)
        
        Returns:
            bool: True si envoyé avec succès
        """
        if not self.enabled:
            logger.warning("WhatsApp service not configured")
            return False
        
        try:
            # Format du message avec emoji selon le type
            emoji_map = {
                "RUPTURE": "🚨",
                "PEREMPTION": "⚠️",
                "SEUIL_BAS": "📉",
                "COMMANDE": "📦",
                "INFO": "ℹ️"
            }
            
            emoji = emoji_map.get(alert_type, "📢")
            formatted_message = f"{emoji} *StockFlow Pro*\n\n{message}"
            
            # Appel API WhatsApp Business (exemple avec Twilio)
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "to": phone_number,
                        "type": "text",
                        "text": {"body": formatted_message}
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"WhatsApp sent to {phone_number}")
                    return True
                else:
                    logger.error(f"WhatsApp failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"WhatsApp error: {str(e)}")
            return False
    
    async def send_stock_alert(
        self,
        phone_number: str,
        article_designation: str,
        stock_actuel: int,
        stock_min: int
    ) -> bool:
        """Envoyer une alerte de stock faible"""
        message = (
            f"⚠️ *Alerte Stock Faible*\n\n"
            f"Article: {article_designation}\n"
            f"Stock actuel: {stock_actuel}\n"
            f"Seuil minimum: {stock_min}\n\n"
            f"Action recommandée: Passer une commande"
        )
        return await self.send_alert(phone_number, message, "SEUIL_BAS")
    
    async def send_rupture_alert(
        self,
        phone_number: str,
        article_designation: str
    ) -> bool:
        """Envoyer une alerte de rupture de stock"""
        message = (
            f"🚨 *RUPTURE DE STOCK*\n\n"
            f"Article: {article_designation}\n"
            f"Stock: 0\n\n"
            f"⚠️ Action urgente requise!"
        )
        return await self.send_alert(phone_number, message, "RUPTURE")
    
    async def send_peremption_alert(
        self,
        phone_number: str,
        article_designation: str,
        jours_restants: int
    ) -> bool:
        """Envoyer une alerte de péremption proche"""
        message = (
            f"⏰ *Alerte Péremption*\n\n"
            f"Article: {article_designation}\n"
            f"Expire dans: {jours_restants} jours\n\n"
            f"Pensez à écouler le stock rapidement"
        )
        return await self.send_alert(phone_number, message, "PEREMPTION")
