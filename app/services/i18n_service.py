"""
Complete Localization/i18n System - Production Grade
Supports: French, Arabic
"""

from typing import Dict, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SupportedLanguage(str, Enum):
    FRENCH = "fr"
    ARABIC = "ar"
    ENGLISH = "en"


class TranslationService:
    """Production-grade translation service"""
    
    # Core translations
    TRANSLATIONS = {
        "ERRORS": {
            "fr": {
                "unauthorized": "Non autorisé",
                "forbidden": "Accès refusé",
                "not_found": "Non trouvé",
                "invalid_data": "Données invalides",
                "rate_limit": "Trop de requêtes, réessayez plus tard",
                "internal_error": "Erreur serveur interne",
                "invalid_credentials": "Identifiants invalides",
                "email_exists": "Cet email existe déjà",
                "weak_password": "Le mot de passe est trop faible",
                "session_expired": "Votre session a expiré",
                "insufficient_stock": "Stock insuffisant",
                "duplicate_alert": "Alerte en double",
                "access_denied_warehouse": "Vous n'avez pas accès à ce magasin",
                "access_denied_article": "Article non trouvé ou accès refusé",
                "access_denied_enterprise": "Vous n'avez pas accès à cette entreprise",
                "admin_only": "Seul un administrateur peut effectuer cette action",
            },
            "ar": {
                "unauthorized": "غير مصرح",
                "forbidden": "الوصول مرفوض",
                "not_found": "غير موجود",
                "invalid_data": "بيانات غير صحيحة",
                "rate_limit": "عدد الطلبات كثير جدا، حاول لاحقا",
                "internal_error": "خطأ في الخادم",
                "invalid_credentials": "بيانات دخول غير صحيحة",
                "email_exists": "هذا البريد الإلكتروني موجود بالفعل",
                "weak_password": "كلمة المرور ضعيفة",
                "session_expired": "انتهت جلستك",
                "insufficient_stock": "مخزون غير كافي",
                "duplicate_alert": "تنبيه مكرر",
                "access_denied_warehouse": "ليس لديك إمكانية الوصول إلى هذا المستودع",
                "access_denied_article": "العنصر غير موجود أو الوصول مرفوض",
                "access_denied_enterprise": "ليس لديك إمكانية الوصول إلى هذه الشركة",
                "admin_only": "يمكن فقط للمسؤول تنفيذ هذا الإجراء",
            }
        },
        "MESSAGES": {
            "fr": {
                "welcome": "Bienvenue",
                "success": "Succès",
                "article_created": "Article créé avec succès",
                "article_updated": "Article mis à jour avec succès",
                "article_deleted": "Article supprimé avec succès",
                "stock_alert": "Alerte de stock bas",
                "low_stock": "Stock faible",
                "out_of_stock": "Rupture de stock",
                "expiring_soon": "Expiration imminente",
                "login_successful": "Connexion réussie",
                "logout_successful": "Déconnexion réussie",
                "password_changed": "Mot de passe changé avec succès",
                "profile_updated": "Profil mis à jour avec succès",
                "export_ready": "Votre export est prêt",
                "import_successful": "Importation réussie",
            },
            "ar": {
                "welcome": "أهلا وسهلا",
                "success": "نجاح",
                "article_created": "تم إنشاء العنصر بنجاح",
                "article_updated": "تم تحديث العنصر بنجاح",
                "article_deleted": "تم حذف العنصر بنجاح",
                "stock_alert": "تنبيه مخزون منخفض",
                "low_stock": "مخزون منخفض",
                "out_of_stock": "غير متوفر",
                "expiring_soon": "سينتهي قريبا",
                "login_successful": "تم تسجيل الدخول بنجاح",
                "logout_successful": "تم تسجيل الخروج بنجاح",
                "password_changed": "تم تغيير كلمة المرور بنجاح",
                "profile_updated": "تم تحديث الملف الشخصي بنجاح",
                "export_ready": "التصدير جاهز",
                "import_successful": "تم الاستيراد بنجاح",
            }
        },
        "LABELS": {
            "fr": {
                "articles": "Articles",
                "warehouses": "Magasins",
                "suppliers": "Fournisseurs",
                "inventory": "Inventaire",
                "sales": "Ventes",
                "purchases": "Achats",
                "reports": "Rapports",
                "settings": "Paramètres",
                "users": "Utilisateurs",
                "dashboard": "Tableau de bord",
                "code": "Code",
                "designation": "Désignation",
                "quantity": "Quantité",
                "price": "Prix",
                "date": "Date",
                "status": "Statut",
                "actions": "Actions",
                "edit": "Modifier",
                "delete": "Supprimer",
                "create": "Créer",
                "search": "Rechercher",
                "filter": "Filtrer",
                "export": "Exporter",
                "import": "Importer",
            },
            "ar": {
                "articles": "العناصر",
                "warehouses": "المستودعات",
                "suppliers": "الموردين",
                "inventory": "المخزون",
                "sales": "المبيعات",
                "purchases": "المشتريات",
                "reports": "التقارير",
                "settings": "الإعدادات",
                "users": "المستخدمون",
                "dashboard": "لوحة القيادة",
                "code": "الكود",
                "designation": "المسمى",
                "quantity": "الكمية",
                "price": "السعر",
                "date": "التاريخ",
                "status": "الحالة",
                "actions": "الإجراءات",
                "edit": "تحرير",
                "delete": "حذف",
                "create": "إنشاء",
                "search": "بحث",
                "filter": "تصفية",
                "export": "تصدير",
                "import": "استيراد",
            }
        },
        "ALERTS": {
            "fr": {
                "stock_critical": "ALERTE CRITIQUE: {article} en rupture de stock",
                "stock_low": "AVERTISSEMENT: Stock faible pour {article}",
                "expiration_warning": "URGENT: {article} expire le {date}",
                "overstock": "SURSTOCK: {article} ({quantity} unités)",
                "price_change": "Prix modifié pour {article}",
                "supplier_delay": "Retard fournisseur: {supplier}",
            },
            "ar": {
                "stock_critical": "تنبيه حرج: {article} غير متوفر",
                "stock_low": "تحذير: مخزون منخفض لـ {article}",
                "expiration_warning": "عاجل: {article} ينتهي في {date}",
                "overstock": "مخزون زائد: {article} ({quantity} وحدة)",
                "price_change": "تم تعديل السعر لـ {article}",
                "supplier_delay": "تأخير الموردين: {supplier}",
            }
        }
    }
    
    @staticmethod
    def translate(
        key: str,
        language: SupportedLanguage = SupportedLanguage.FRENCH,
        category: str = "MESSAGES",
        **kwargs
    ) -> str:
        """
        Translate a key
        
        Args:
            key: Translation key (e.g., "success", "not_found")
            language: Target language (default: FRENCH)
            category: Translation category (ERRORS, MESSAGES, LABELS, ALERTS)
            **kwargs: Variables to format into the translation
        
        Returns:
            Translated string
        """
        try:
            lang_code = language.value if isinstance(language, SupportedLanguage) else language
            
            # Get translation
            if category not in TranslationService.TRANSLATIONS:
                logger.warning(f"Unknown category: {category}")
                return key
            
            category_dict = TranslationService.TRANSLATIONS[category]
            
            if lang_code not in category_dict:
                # Fallback to French
                lang_code = "fr"
            
            if key not in category_dict.get(lang_code, {}):
                logger.warning(f"Unknown translation key: {category}.{key}")
                return key
            
            translation = category_dict[lang_code][key]
            
            # Format with variables
            if kwargs:
                translation = translation.format(**kwargs)
            
            return translation
        
        except Exception as e:
            logger.error(f"Translation error for key {key}: {e}")
            return key
    
    @staticmethod
    def translate_error(
        error_key: str,
        language: SupportedLanguage = SupportedLanguage.FRENCH,
        **kwargs
    ) -> str:
        """Translate an error message"""
        return TranslationService.translate(
            error_key,
            language,
            "ERRORS",
            **kwargs
        )
    
    @staticmethod
    def translate_message(
        message_key: str,
        language: SupportedLanguage = SupportedLanguage.FRENCH,
        **kwargs
    ) -> str:
        """Translate a success/info message"""
        return TranslationService.translate(
            message_key,
            language,
            "MESSAGES",
            **kwargs
        )
    
    @staticmethod
    def translate_label(
        label_key: str,
        language: SupportedLanguage = SupportedLanguage.FRENCH
    ) -> str:
        """Translate a UI label"""
        return TranslationService.translate(
            label_key,
            language,
            "LABELS"
        )
    
    @staticmethod
    def translate_alert(
        alert_key: str,
        language: SupportedLanguage = SupportedLanguage.FRENCH,
        **kwargs
    ) -> str:
        """Translate an alert message"""
        return TranslationService.translate(
            alert_key,
            language,
            "ALERTS",
            **kwargs
        )
    
    @staticmethod
    def get_user_language(user: Dict) -> SupportedLanguage:
        """
        Get user's preferred language from JWT token
        
        Falls back to FRENCH if not specified
        """
        lang = user.get("language", "fr")
        
        try:
            return SupportedLanguage(lang)
        except ValueError:
            logger.warning(f"Unknown language: {lang}, falling back to French")
            return SupportedLanguage.FRENCH
    
    @staticmethod
    def get_available_languages() -> List[Dict]:
        """Get list of available languages"""
        return [
            {
                "code": SupportedLanguage.FRENCH.value,
                "name": "Français",
                "native_name": "Français"
            },
            {
                "code": SupportedLanguage.ARABIC.value,
                "name": "Arabic",
                "native_name": "العربية"
            },
            {
                "code": SupportedLanguage.ENGLISH.value,
                "name": "English",
                "native_name": "English"
            }
        ]
    
    @staticmethod
    def translate_response(
        response: Dict,
        language: SupportedLanguage = SupportedLanguage.FRENCH
    ) -> Dict:
        """
        Recursively translate all translatable fields in response
        Looks for 'i18n_key' field to identify translatable strings
        """
        try:
            if isinstance(response, dict):
                translated = {}
                for key, value in response.items():
                    if key == "i18n_key" and isinstance(value, str):
                        # Translate this field
                        translated_value = TranslationService.translate(value, language)
                        translated[key.replace("i18n_", "")] = translated_value
                    elif isinstance(value, (dict, list)):
                        translated[key] = TranslationService.translate_response(value, language)
                    else:
                        translated[key] = value
                return translated
            
            elif isinstance(response, list):
                return [
                    TranslationService.translate_response(item, language)
                    for item in response
                ]
            
            else:
                return response
        
        except Exception as e:
            logger.error(f"Response translation error: {e}")
            return response
