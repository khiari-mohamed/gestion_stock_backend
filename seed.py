import asyncio
from prisma import Prisma
from app.core.security import get_password_hash

async def seed_database():
    prisma = Prisma()
    await prisma.connect()
    
    print("🌱 Seeding database...")
    
    # Créer une entreprise
    entreprise = await prisma.entreprise.create(
        data={
            "nom": "Épicerie Moderne",
            "matricule_fiscal": "1234567A",
            "adresse": "Avenue Habib Bourguiba, Tunis",
            "telephone": "+216 71 123 456",
            "email": "contact@epicerie-moderne.tn"
        }
    )
    print(f"✅ Entreprise créée: {entreprise.nom}")
    
    # Créer un magasin
    magasin = await prisma.magasin.create(
        data={
            "nom": "Magasin Principal",
            "adresse": "Centre-ville, Tunis",
            "telephone": "+216 71 123 456",
            "is_principal": True,
            "entreprise_id": entreprise.id
        }
    )
    print(f"✅ Magasin créé: {magasin.nom}")
    
    # Créer un utilisateur patron
    user_patron = await prisma.user.create(
        data={
            "email": "patron@epicerie.tn",
            "password_hash": get_password_hash("password123"),
            "nom": "Ben Ali",
            "prenom": "Mohamed",
            "telephone": "+216 98 123 456",
            "langue": "fr",
            "role": "patron",
            "entreprise_id": entreprise.id
        }
    )
    print(f"✅ Utilisateur patron créé: {user_patron.email}")
    
    # Créer un utilisateur employé
    user_employe = await prisma.user.create(
        data={
            "email": "employe@epicerie.tn",
            "password_hash": get_password_hash("password123"),
            "nom": "Trabelsi",
            "prenom": "Fatma",
            "telephone": "+216 98 654 321",
            "langue": "fr",
            "role": "employe",
            "entreprise_id": entreprise.id
        }
    )
    print(f"✅ Utilisateur employé créé: {user_employe.email}")
    
    # Créer des fournisseurs
    fournisseur1 = await prisma.fournisseur.create(
        data={
            "nom": "Délice Danone",
            "type": "formel",
            "telephone": "+216 71 234 567",
            "email": "contact@delice.tn",
            "adresse": "Zone industrielle, Ben Arous",
            "matricule_fiscal": "9876543B",
            "delai_livraison": 2,
            "score_fiabilite": 8.5,
            "entreprise_id": entreprise.id
        }
    )
    print(f"✅ Fournisseur créé: {fournisseur1.nom}")
    
    # Créer des articles
    articles_data = [
        {
            "code": "LAI001",
            "designation": "Lait Délice 1L",
            "description": "Lait frais pasteurisé",
            "code_barre": "6191510000011",
            "unite": "litre",
            "prix_achat": 1.5,
            "prix_vente": 2.0,
            "stock_actuel": 50,
            "stock_min": 20,
            "stock_max": 100,
            "magasin_id": magasin.id
        },
        {
            "code": "YAO001",
            "designation": "Yaourt Délice Nature",
            "description": "Yaourt nature 125g",
            "code_barre": "6191510000028",
            "unite": "unite",
            "prix_achat": 0.4,
            "prix_vente": 0.6,
            "stock_actuel": 15,
            "stock_min": 30,
            "stock_max": 150,
            "magasin_id": magasin.id
        },
        {
            "code": "HUI001",
            "designation": "Huile d'Olive 1L",
            "description": "Huile d'olive extra vierge",
            "code_barre": "6191510000035",
            "unite": "litre",
            "prix_achat": 8.0,
            "prix_vente": 12.0,
            "stock_actuel": 25,
            "stock_min": 10,
            "stock_max": 50,
            "magasin_id": magasin.id
        },
        {
            "code": "RIZ001",
            "designation": "Riz Basmati 1kg",
            "description": "Riz basmati de qualité supérieure",
            "code_barre": "6191510000042",
            "unite": "kg",
            "prix_achat": 3.5,
            "prix_vente": 5.0,
            "stock_actuel": 5,
            "stock_min": 15,
            "stock_max": 80,
            "magasin_id": magasin.id
        },
        {
            "code": "PAT001",
            "designation": "Pâtes Alimentaires 500g",
            "description": "Pâtes spaghetti",
            "code_barre": "6191510000059",
            "unite": "paquet",
            "prix_achat": 0.8,
            "prix_vente": 1.2,
            "stock_actuel": 0,
            "stock_min": 20,
            "stock_max": 100,
            "magasin_id": magasin.id
        }
    ]
    
    for article_data in articles_data:
        article = await prisma.article.create(data=article_data)
        print(f"✅ Article créé: {article.designation} (Stock: {article.stock_actuel})")
    
    # Créer des jours fériés tunisiens 2025
    jours_feries = [
        {"date": "2025-01-01", "nom": "Nouvel An", "impact_estime": 1.2},
        {"date": "2025-03-20", "nom": "Fête de l'Indépendance", "impact_estime": 1.3},
        {"date": "2025-03-30", "nom": "Aïd el-Fitr (estimé)", "impact_estime": 2.0},
        {"date": "2025-04-09", "nom": "Journée des Martyrs", "impact_estime": 1.1},
        {"date": "2025-05-01", "nom": "Fête du Travail", "impact_estime": 1.0},
        {"date": "2025-06-06", "nom": "Aïd el-Adha (estimé)", "impact_estime": 2.5},
        {"date": "2025-07-25", "nom": "Fête de la République", "impact_estime": 1.2},
        {"date": "2025-08-13", "nom": "Journée de la Femme", "impact_estime": 1.0},
    ]
    
    for jour in jours_feries:
        await prisma.jourferie.create(data=jour)
    print(f"✅ {len(jours_feries)} jours fériés créés")
    
    await prisma.disconnect()
    print("\n🎉 Seeding terminé avec succès!")
    print("\n📝 Comptes de test créés:")
    print("   Patron: patron@epicerie.tn / password123")
    print("   Employé: employe@epicerie.tn / password123")

if __name__ == "__main__":
    asyncio.run(seed_database())
