# StockFlow Pro - Backend API

Backend FastAPI pour StockFlow Pro - Gestion de stock intelligente pour PME tunisiennes.

## 🚀 Stack Technique

- **Framework**: FastAPI
- **ORM**: Prisma (Python)
- **Base de données**: PostgreSQL
- **Cache**: Redis
- **Authentification**: JWT (python-jose)

## 📋 Prérequis

- Python 3.11+
- Docker & Docker Compose
- Node.js 18+ (pour Prisma CLI)

## 🛠️ Installation

### 1. Cloner le projet et installer les dépendances

```bash
cd backend
pip install -r requirements.txt
```

### 2. Installer Prisma CLI

```bash
npm install -g prisma
```

### 3. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Modifier le fichier `.env` avec vos configurations.

### 4. Démarrer avec Docker Compose (Recommandé)

```bash
# Depuis la racine du projet
docker-compose up -d
```

Cela démarre :
- PostgreSQL (port 5432)
- Redis (port 6379)
- Backend API (port 8000)

### 5. Générer le client Prisma

```bash
cd backend
prisma generate
```

### 6. Créer la base de données

```bash
prisma db push
```

## 🎯 Démarrage Manuel (Sans Docker)

```bash
# Démarrer PostgreSQL et Redis localement
# Puis :
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 Documentation API

Une fois l'application démarrée, accédez à :

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🗂️ Structure du Projet

```
backend/
├── app/
│   ├── api/              # Routes API
│   │   ├── auth.py       # Authentification
│   │   ├── articles.py   # Gestion articles
│   │   ├── mouvements.py # Mouvements de stock
│   │   └── dashboard.py  # Tableau de bord
│   ├── core/             # Configuration
│   │   ├── config.py     # Variables d'environnement
│   │   ├── database.py   # Connexion Prisma
│   │   └── security.py   # JWT & hashing
│   ├── schemas/          # Modèles Pydantic
│   ├── services/         # Logique métier
│   └── main.py           # Point d'entrée FastAPI
├── prisma/
│   └── schema.prisma     # Schéma de base de données
├── requirements.txt
└── Dockerfile
```

## 🔑 Endpoints Principaux (MVP Phase 1)

### Authentification
- `POST /api/v1/auth/register` - Créer un compte
- `POST /api/v1/auth/login` - Se connecter

### Articles
- `POST /api/v1/articles/` - Créer un article
- `GET /api/v1/articles/{id}` - Récupérer un article
- `GET /api/v1/articles/magasin/{magasin_id}` - Lister les articles
- `GET /api/v1/articles/magasin/{magasin_id}/faibles` - Articles en stock faible
- `PUT /api/v1/articles/{id}` - Modifier un article
- `DELETE /api/v1/articles/{id}` - Supprimer un article

### Mouvements de Stock
- `POST /api/v1/mouvements/` - Créer un mouvement (entrée/sortie)
- `GET /api/v1/mouvements/article/{article_id}` - Historique d'un article
- `GET /api/v1/mouvements/magasin/{magasin_id}` - Tous les mouvements

### Dashboard
- `GET /api/v1/dashboard/magasin/{magasin_id}` - Statistiques du magasin

## 🧪 Tests

```bash
pytest
```

## 📦 Fonctionnalités MVP (Phase 1)

✅ CRUD Articles  
✅ Mouvements de stock (entrée/sortie/ajustement/retour)  
✅ Mise à jour automatique du stock  
✅ Dashboard simple (valeur stock, articles faibles)  
✅ Alertes de seuil bas  
✅ Authentification JWT  
✅ 1 magasin par compte  

🚫 Exclus du MVP : IA, multi-magasin, scoring fournisseur

## 🔐 Sécurité

- Mots de passe hashés avec bcrypt
- Authentification JWT
- HTTPS en production
- Validation des données avec Pydantic

## 📝 Licence

Propriétaire - StockFlow Pro © 2025
