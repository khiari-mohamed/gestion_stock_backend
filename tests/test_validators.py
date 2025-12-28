import pytest
from app.utils.validators import (
    validate_phone_tunisie,
    validate_matricule_fiscal,
    validate_code_barre,
    validate_email,
    validate_prix
)


class TestPhoneValidation:
    """Tests pour la validation des numéros de téléphone tunisiens"""
    
    def test_valid_phone_with_country_code(self):
        """Test numéro valide avec indicatif +216"""
        assert validate_phone_tunisie("+21612345678") == True
        assert validate_phone_tunisie("+21698765432") == True
    
    def test_valid_phone_without_country_code(self):
        """Test numéro valide sans indicatif"""
        assert validate_phone_tunisie("12345678") == True
        assert validate_phone_tunisie("98765432") == True
    
    def test_invalid_phone_too_short(self):
        """Test numéro trop court"""
        assert validate_phone_tunisie("1234567") == False
        assert validate_phone_tunisie("+2161234567") == False
    
    def test_invalid_phone_too_long(self):
        """Test numéro trop long"""
        assert validate_phone_tunisie("123456789") == False
        assert validate_phone_tunisie("+216123456789") == False
    
    def test_invalid_phone_wrong_country_code(self):
        """Test mauvais indicatif pays"""
        assert validate_phone_tunisie("+33612345678") == False
        assert validate_phone_tunisie("+1234567890") == False
    
    def test_invalid_phone_non_numeric(self):
        """Test caractères non numériques"""
        assert validate_phone_tunisie("12-34-56-78") == False
        assert validate_phone_tunisie("12 34 56 78") == False
        assert validate_phone_tunisie("abcdefgh") == False


class TestMatriculeFiscalValidation:
    """Tests pour la validation du matricule fiscal tunisien"""
    
    def test_valid_matricule_fiscal(self):
        """Test matricule fiscal valide (7 chiffres + 1 lettre)"""
        assert validate_matricule_fiscal("1234567A") == True
        assert validate_matricule_fiscal("9876543Z") == True
        assert validate_matricule_fiscal("0000001B") == True
    
    def test_valid_matricule_with_spaces(self):
        """Test matricule avec espaces (devrait être nettoyé)"""
        assert validate_matricule_fiscal("1234567 A") == True
        assert validate_matricule_fiscal(" 1234567A ") == True
    
    def test_invalid_matricule_too_short(self):
        """Test matricule trop court"""
        assert validate_matricule_fiscal("123456A") == False
        assert validate_matricule_fiscal("12345A") == False
    
    def test_invalid_matricule_too_long(self):
        """Test matricule trop long"""
        assert validate_matricule_fiscal("12345678A") == False
        assert validate_matricule_fiscal("1234567AB") == False
    
    def test_invalid_matricule_no_letter(self):
        """Test matricule sans lettre"""
        assert validate_matricule_fiscal("12345678") == False
    
    def test_invalid_matricule_multiple_letters(self):
        """Test matricule avec plusieurs lettres"""
        assert validate_matricule_fiscal("123456AB") == False
    
    def test_invalid_matricule_letter_first(self):
        """Test matricule avec lettre au début"""
        assert validate_matricule_fiscal("A1234567") == False


class TestCodeBarreValidation:
    """Tests pour la validation des codes-barres"""
    
    def test_valid_ean13(self):
        """Test code-barre EAN-13 valide"""
        assert validate_code_barre("1234567890123") == True
    
    def test_valid_ean8(self):
        """Test code-barre EAN-8 valide"""
        assert validate_code_barre("12345678") == True
    
    def test_valid_custom_code(self):
        """Test code personnalisé valide"""
        assert validate_code_barre("ART-001") == True
        assert validate_code_barre("PROD_2024_001") == True
    
    def test_invalid_code_too_short(self):
        """Test code trop court"""
        assert validate_code_barre("123") == False
    
    def test_invalid_code_empty(self):
        """Test code vide"""
        assert validate_code_barre("") == False
        assert validate_code_barre("   ") == False
    
    def test_invalid_code_special_chars(self):
        """Test code avec caractères spéciaux invalides"""
        assert validate_code_barre("ART@001") == False
        assert validate_code_barre("PROD#123") == False


class TestEmailValidation:
    """Tests pour la validation des emails"""
    
    def test_valid_email(self):
        """Test email valide"""
        assert validate_email("user@example.com") == True
        assert validate_email("test.user@company.tn") == True
        assert validate_email("admin+tag@domain.co.uk") == True
    
    def test_invalid_email_no_at(self):
        """Test email sans @"""
        assert validate_email("userexample.com") == False
    
    def test_invalid_email_no_domain(self):
        """Test email sans domaine"""
        assert validate_email("user@") == False
        assert validate_email("user@.com") == False
    
    def test_invalid_email_spaces(self):
        """Test email avec espaces"""
        assert validate_email("user @example.com") == False
        assert validate_email("user@ example.com") == False
    
    def test_invalid_email_empty(self):
        """Test email vide"""
        assert validate_email("") == False


class TestPrixValidation:
    """Tests pour la validation des prix"""
    
    def test_valid_prix_positive(self):
        """Test prix positif valide"""
        assert validate_prix(10.0) == True
        assert validate_prix(100.5) == True
        assert validate_prix(0.001) == True
    
    def test_valid_prix_zero(self):
        """Test prix zéro (peut être valide pour articles gratuits)"""
        assert validate_prix(0.0) == True
    
    def test_invalid_prix_negative(self):
        """Test prix négatif"""
        assert validate_prix(-10.0) == False
        assert validate_prix(-0.01) == False
    
    def test_invalid_prix_none(self):
        """Test prix None"""
        assert validate_prix(None) == False
    
    def test_prix_precision_tunisian(self):
        """Test précision des prix tunisiens (3 décimales)"""
        prix = 10.123
        prix_arrondi = round(prix, 3)
        assert prix_arrondi == 10.123
        
        prix2 = 10.1234
        prix2_arrondi = round(prix2, 3)
        assert prix2_arrondi == 10.123


class TestTunisianBusinessRules:
    """Tests pour les règles métier tunisiennes"""
    
    def test_tva_rate_standard(self):
        """Test taux de TVA standard tunisien (19%)"""
        tva_standard = 0.19
        montant_ht = 100.0
        tva = round(montant_ht * tva_standard, 3)
        montant_ttc = round(montant_ht + tva, 3)
        
        assert tva == 19.0
        assert montant_ttc == 119.0
    
    def test_tva_rate_reduced(self):
        """Test taux de TVA réduit (7% pour certains produits)"""
        tva_reduit = 0.07
        montant_ht = 100.0
        tva = round(montant_ht * tva_reduit, 3)
        montant_ttc = round(montant_ht + tva, 3)
        
        assert tva == 7.0
        assert montant_ttc == 107.0
    
    def test_currency_precision_tnd(self):
        """Test précision monétaire tunisienne (3 décimales)"""
        montant = 123.4567
        montant_arrondi = round(montant, 3)
        
        assert montant_arrondi == 123.457
    
    def test_working_days_tunisia(self):
        """Test jours ouvrables en Tunisie (Lundi-Samedi)"""
        jours_ouvres = ["LUNDI", "MARDI", "MERCREDI", "JEUDI", "VENDREDI", "SAMEDI"]
        jours_fermes = ["DIMANCHE"]
        
        assert len(jours_ouvres) == 6
        assert "DIMANCHE" not in jours_ouvres
