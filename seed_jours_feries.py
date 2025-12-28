"""
Seed des jours fériés tunisiens 2024-2025
"""
import asyncio
from datetime import datetime
from app.core.database import prisma

JOURS_FERIES_2024_2025 = [
    # 2024
    {"date": datetime(2024, 1, 1), "nom": "Nouvel An", "type": "NATIONALE", "impact_estime": 1.2},
    {"date": datetime(2024, 1, 14), "nom": "Révolution et de la Jeunesse", "type": "NATIONALE", "impact_estime": 1.0},
    {"date": datetime(2024, 3, 20), "nom": "Fête de l'Indépendance", "type": "NATIONALE", "impact_estime": 1.0},
    {"date": datetime(2024, 4, 9), "nom": "Jour des Martyrs", "type": "NATIONALE", "impact_estime": 1.0},
    {"date": datetime(2024, 4, 10), "nom": "Aïd el-Fitr", "type": "RELIGIEUSE", "impact_estime": 1.8},
    {"date": datetime(2024, 4, 11), "nom": "Aïd el-Fitr (2ème jour)", "type": "RELIGIEUSE", "impact_estime": 1.5},
    {"date": datetime(2024, 5, 1), "nom": "Fête du Travail", "type": "NATIONALE", "impact_estime": 1.0},
    {"date": datetime(2024, 6, 16), "nom": "Aïd el-Adha", "type": "RELIGIEUSE", "impact_estime": 2.0},
    {"date": datetime(2024, 6, 17), "nom": "Aïd el-Adha (2ème jour)", "type": "RELIGIEUSE", "impact_estime": 1.7},
    {"date": datetime(2024, 7, 7), "nom": "Nouvel An Hégirien", "type": "RELIGIEUSE", "impact_estime": 1.1},
    {"date": datetime(2024, 7, 25), "nom": "Fête de la République", "type": "NATIONALE", "impact_estime": 1.0},
    {"date": datetime(2024, 8, 13), "nom": "Fête de la Femme", "type": "NATIONALE", "impact_estime": 1.0},
    {"date": datetime(2024, 9, 15), "nom": "Mawlid (Naissance du Prophète)", "type": "RELIGIEUSE", "impact_estime": 1.2},
    {"date": datetime(2024, 10, 15), "nom": "Journée de l'Évacuation", "type": "NATIONALE", "impact_estime": 1.0},
    
    # 2025
    {"date": datetime(2025, 1, 1), "nom": "Nouvel An", "type": "NATIONALE", "impact_estime": 1.2},
    {"date": datetime(2025, 1, 14), "nom": "Révolution et de la Jeunesse", "type": "NATIONALE", "impact_estime": 1.0},
    {"date": datetime(2025, 3, 20), "nom": "Fête de l'Indépendance", "type": "NATIONALE", "impact_estime": 1.0},
    {"date": datetime(2025, 3, 30), "nom": "Aïd el-Fitr", "type": "RELIGIEUSE", "impact_estime": 1.8},
    {"date": datetime(2025, 3, 31), "nom": "Aïd el-Fitr (2ème jour)", "type": "RELIGIEUSE", "impact_estime": 1.5},
    {"date": datetime(2025, 4, 9), "nom": "Jour des Martyrs", "type": "NATIONALE", "impact_estime": 1.0},
    {"date": datetime(2025, 5, 1), "nom": "Fête du Travail", "type": "NATIONALE", "impact_estime": 1.0},
    {"date": datetime(2025, 6, 6), "nom": "Aïd el-Adha", "type": "RELIGIEUSE", "impact_estime": 2.0},
    {"date": datetime(2025, 6, 7), "nom": "Aïd el-Adha (2ème jour)", "type": "RELIGIEUSE", "impact_estime": 1.7},
    {"date": datetime(2025, 6, 26), "nom": "Nouvel An Hégirien", "type": "RELIGIEUSE", "impact_estime": 1.1},
    {"date": datetime(2025, 7, 25), "nom": "Fête de la République", "type": "NATIONALE", "impact_estime": 1.0},
    {"date": datetime(2025, 8, 13), "nom": "Fête de la Femme", "type": "NATIONALE", "impact_estime": 1.0},
    {"date": datetime(2025, 9, 4), "nom": "Mawlid (Naissance du Prophète)", "type": "RELIGIEUSE", "impact_estime": 1.2},
    {"date": datetime(2025, 10, 15), "nom": "Journée de l'Évacuation", "type": "NATIONALE", "impact_estime": 1.0},
]

async def seed_jours_feries():
    """Seed les jours fériés tunisiens"""
    await prisma.connect()
    
    print("Seeding jours fériés tunisiens...")
    
    created = 0
    skipped = 0
    
    for jour in JOURS_FERIES_2024_2025:
        existing = await prisma.jourferie.find_unique(where={"date": jour["date"]})
        
        if not existing:
            await prisma.jourferie.create(
                data={
                    "date": jour["date"],
                    "nom": jour["nom"],
                    "type": jour["type"],
                    "impact_estime": jour["impact_estime"]
                }
            )
            created += 1
            print(f"✓ {jour['nom']} - {jour['date'].strftime('%d/%m/%Y')}")
        else:
            skipped += 1
    
    print(f"\nTerminé: {created} créés, {skipped} ignorés")
    
    await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(seed_jours_feries())
