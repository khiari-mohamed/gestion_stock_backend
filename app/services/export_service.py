from typing import List
import pandas as pd
from io import BytesIO
from datetime import datetime


class ExportService:
    """Service pour générer des exports PDF et Excel"""
    
    def export_mouvements_excel(self, mouvements: List) -> bytes:
        """Exporter les mouvements en Excel"""
        data = []
        for m in mouvements:
            data.append({
                "Date": m.date_mouvement.strftime("%d/%m/%Y %H:%M"),
                "Type": m.type,
                "Article": m.article.designation if hasattr(m, 'article') else "",
                "Code": m.article.code if hasattr(m, 'article') else "",
                "Quantité": m.quantite,
                "Prix Unitaire": m.prix_unitaire or 0,
                "Valeur Totale": m.valeur_totale or 0,
                "Motif": m.motif or ""
            })
        
        df = pd.DataFrame(data)
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        return buffer.getvalue()
    
    def export_stock_pdf(self, articles: List, magasin_id: str) -> bytes:
        """Exporter l'état du stock en PDF (placeholder - nécessite reportlab)"""
        # TODO: Implémenter avec reportlab pour génération PDF
        # Pour le MVP, retourner un Excel
        data = []
        for a in articles:
            data.append({
                "Code": a.code,
                "Désignation": a.designation,
                "Stock Actuel": a.stock_actuel,
                "Stock Min": a.stock_min,
                "Prix Achat": a.prix_achat,
                "Valeur": a.stock_actuel * a.prix_achat
            })
        
        df = pd.DataFrame(data)
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        return buffer.getvalue()
    
    def export_valorisation_excel(self, articles: List) -> bytes:
        """Exporter la valorisation du stock (format comptabilité tunisienne)"""
        data = []
        total_valeur = 0
        
        for a in articles:
            valeur = a.stock_actuel * a.prix_achat
            tva = valeur * (a.tva_taux or 0.19)
            total_valeur += valeur
            
            data.append({
                "Code Article": a.code,
                "Désignation": a.designation,
                "Quantité en Stock": a.stock_actuel,
                "Prix Achat HT (DT)": round(a.prix_achat, 3),
                "Valeur Stock HT (DT)": round(valeur, 3),
                "Taux TVA": f"{(a.tva_taux or 0.19) * 100}%",
                "TVA (DT)": round(tva, 3),
                "Valeur TTC (DT)": round(valeur + tva, 3)
            })
        
        df = pd.DataFrame(data)
        
        # Ajouter ligne de total
        total_row = pd.DataFrame([{
            "Code Article": "TOTAL",
            "Désignation": "",
            "Quantité en Stock": sum(a.stock_actuel for a in articles),
            "Prix Achat HT (DT)": "",
            "Valeur Stock HT (DT)": round(total_valeur, 3),
            "Taux TVA": "",
            "TVA (DT)": round(sum(a.stock_actuel * a.prix_achat * (a.tva_taux or 0.19) for a in articles), 3),
            "Valeur TTC (DT)": round(sum(a.stock_actuel * a.prix_achat * (1 + (a.tva_taux or 0.19)) for a in articles), 3)
        }])
        
        df = pd.concat([df, total_row], ignore_index=True)
        
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Valorisation Stock')
            
            # Formater le fichier
            worksheet = writer.sheets['Valorisation Stock']
            for column in worksheet.columns:
                max_length = 0
                column = [cell for cell in column]
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
        
        return buffer.getvalue()
