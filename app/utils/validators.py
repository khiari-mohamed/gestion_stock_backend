import re
from typing import Optional

def validate_phone_tunisie(phone: str) -> bool:
    """
    Valider un numéro de téléphone tunisien
    Format: +216 XX XXX XXX ou 216XXXXXXXX ou XXXXXXXX
    """
    pattern = r'^(\+216|216)?[2-9]\d{7}$'
    return bool(re.match(pattern, phone.replace(" ", "")))

def validate_matricule_fiscal(matricule: str) -> bool:
    """
    Valider un matricule fiscal tunisien
    Format: XXXXXXXL (7 chiffres + 1 lettre)
    """
    pattern = r'^\d{7}[A-Z]$'
    return bool(re.match(pattern, matricule.upper()))

def validate_code_barre(code: str) -> bool:
    """
    Valider un code-barres (EAN-13 ou EAN-8)
    """
    if len(code) not in [8, 13]:
        return False
    return code.isdigit()

def sanitize_string(text: Optional[str]) -> Optional[str]:
    """
    Nettoyer une chaîne de caractères
    """
    if not text:
        return None
    return text.strip()
