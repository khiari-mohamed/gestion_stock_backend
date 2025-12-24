from typing import List
import httpx

class NotificationService:
    """
    Service de notifications (Email, WhatsApp)
    Phase 1 (MVP): Logs uniquement
    Phase 2: Email + WhatsApp Business API
    """
    
    @staticmethod
    async def send_email(to: str, subject: str, body: str):
        """
        Envoyer un email
        TODO: Implémenter en Phase 2 avec SendGrid ou AWS SES
        """
        print(f"[EMAIL] To: {to}, Subject: {subject}")
        pass
    
    @staticmethod
    async def send_whatsapp(phone: str, message: str):
        """
        Envoyer un message WhatsApp via Business API
        TODO: Implémenter en Phase 2
        """
        print(f"[WHATSAPP] To: {phone}, Message: {message}")
        pass
    
    @staticmethod
    async def notify_stock_faible(article: dict, user_phone: str):
        """
        Notifier un stock faible
        """
        message = f"⚠️ ALERTE STOCK FAIBLE\n\n"
        message += f"Article: {article['designation']}\n"
        message += f"Stock actuel: {article['stock_actuel']}\n"
        message += f"Seuil minimum: {article['stock_min']}"
        
        # Phase 1: Log uniquement
        print(f"[NOTIFICATION] {message}")
        
        # Phase 2: Envoyer WhatsApp
        # await NotificationService.send_whatsapp(user_phone, message)
    
    @staticmethod
    async def notify_rupture_stock(article: dict, user_phone: str):
        """
        Notifier une rupture de stock
        """
        message = f"🚨 RUPTURE DE STOCK\n\n"
        message += f"Article: {article['designation']}\n"
        message += f"Code: {article['code']}"
        
        print(f"[NOTIFICATION] {message}")
