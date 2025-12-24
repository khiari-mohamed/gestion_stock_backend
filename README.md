# 🚀 StockFlow Pro - Guide de Démarrage Rapide

## 📋 Vue d'ensemble

StockFlow Pro est une solution de gestion de stock intelligente pour les PME tunisiennes, développée selon le cahier des charges strict.

**Phase actuelle**: MVP Phase 1 (Validation)

## ✅ Fonctionnalités Implémentées (MVP)

- ✅ CRUD complet des Articles
- ✅ Gestion des Mouvements de Stock (entrée/sortie/ajustement/retour)
- ✅ Mise à jour automatique du stock
- ✅ Dashboard simple avec KPIs
- ✅ Alertes de stock faible
- ✅ Authentification JWT sécurisée
- ✅ Support 1 magasin par compte
- ✅ Base de données PostgreSQL avec Prisma ORM
- ✅ API REST complète avec FastAPI

## 🛠️ Installation Rapide (Windows)

### Option 1: Avec Docker (Recommandé)

```bash
# 1. Cloner et configurer
git clone <repo>
cd gestion_stock

# 2. Lancer le setup automatique
setup.bat

# 3. Démarrer les services
docker-compose up -d

# 4. Créer la base de données
cd backend
prisma db push

# 5. Insérer les données de test
python seed.py
```

### Option 2: Installation Manuelle

```bash
# 1. Installer les dépendances
cd backend
pip install -r requirements.txt
npm install -g prisma

# 2. Configurer l'environnement
copy .env.example .env
# Éditer .env avec vos paramètres

# 3. Générer le client Prisma
prisma generate

# 4. Démarrer PostgreSQL et Redis localement

# 5. Créer la base de données
prisma db push

# 6. Insérer les données de test
python seed.py

# 7. Lancer l'API
uvicorn app.main:app --reload
```

## 🌐 Accès à l'Application

- **API Backend**: http://localhost:8000
- **Documentation Swagger**: http://localhost:8000/docs
- **Documentation ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔑 Comptes de Test

Après avoir exécuté `seed.py`, vous aurez accès à :

| Rôle | Email | Mot de passe |
|------|-------|--------------|
| Patron | patron@epicerie.tn | password123 |
| Employé | employe@epicerie.tn | password123 |

## 📊 Structure de la Base de Données

Le schéma Prisma implémente le modèle de données complet du cahier des charges :

- **User** → Utilisateurs (patron, employé, comptable)
- **Entreprise** → Entreprises clientes
- **Magasin** → Points de vente/entrepôts
- **Article** → Produits en stock
- **MouvementStock** → Historique des mouvements
- **Fournisseur** → Carnet d'adresses fournisseurs
- **Vente** → Historique des ventes (pour IA future)
- **Prevision** → Prévisions IA (Phase 2)
- **JourFerie** → Jours fériés tunisiens
- **AuditLog** → Traçabilité des actions

## 🔌 Endpoints API Principaux

### Authentification
```http
POST /api/v1/auth/register
POST /api/v1/auth/login
```

### Articles
```http
POST   /api/v1/articles/
GET    /api/v1/articles/{id}
GET    /api/v1/articles/magasin/{magasin_id}
GET    /api/v1/articles/magasin/{magasin_id}/faibles
GET    /api/v1/articles/magasin/{magasin_id}/search?q=lait
PUT    /api/v1/articles/{id}
DELETE /api/v1/articles/{id}
```

### Mouvements de Stock
```http
POST /api/v1/mouvements/
GET  /api/v1/mouvements/article/{article_id}
GET  /api/v1/mouvements/magasin/{magasin_id}
```

### Dashboard
```http
GET /api/v1/dashboard/magasin/{magasin_id}
```

## 📝 Exemple d'Utilisation

### 1. Se connecter
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patron@epicerie.tn",
    "password": "password123"
  }'
```

### 2. Créer un article
```bash
curl -X POST http://localhost:8000/api/v1/articles/ \
  -H "Authorization: Bearer <votre_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "CAF001",
    "designation": "Café Moulu 250g",
    "prix_achat": 4.5,
    "prix_vente": 7.0,
    "stock_min": 10,
    "stock_max": 50,
    "magasin_id": "<magasin_id>"
  }'
```

### 3. Enregistrer une entrée de stock
```bash
curl -X POST http://localhost:8000/api/v1/mouvements/ \
  -H "Authorization: Bearer <votre_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "entree",
    "quantite": 30,
    "prix_unitaire": 4.5,
    "article_id": "<article_id>",
    "magasin_id": "<magasin_id>"
  }'
```

## 🧪 Tests

```bash
cd backend
pytest
```

## 📦 Technologies Utilisées

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Backend | FastAPI | 0.109.0 |
| ORM | Prisma | 0.11.0 |
| Base de données | PostgreSQL | 15 |
| Cache | Redis | 7 |
| Auth | JWT (python-jose) | 3.3.0 |
| Validation | Pydantic | 2.5.3 |

## 🔒 Sécurité

- ✅ Mots de passe hashés avec bcrypt
- ✅ Authentification JWT
- ✅ Validation des données avec Pydantic
- ✅ Protection CORS configurée
- ✅ Variables d'environnement sécurisées

## 📈 Prochaines Étapes (Roadmap)

### Phase 2 - Intelligence (V1.0)
- [ ] Module IA de prévision de la demande
- [ ] Moteur de suggestions de commande
- [ ] Alertes WhatsApp Business API
- [ ] Gestion avancée des fournisseurs

### Phase 3 - Conformité (V1.5)
- [ ] Analytics "Cash Immobilisé"
- [ ] Indicateurs TVA
- [ ] Exports comptables avancés

### Phase 4 - Échelle (V2.0)
- [ ] Gestion multi-magasin
- [ ] API publique
- [ ] Workflow de validation

## 🐛 Dépannage

### Erreur de connexion à la base de données
```bash
# Vérifier que PostgreSQL est démarré
docker ps

# Recréer les containers
docker-compose down
docker-compose up -d
```

### Erreur Prisma Client
```bash
# Régénérer le client
cd backend
prisma generate
```

### Port 8000 déjà utilisé
```bash
# Changer le port dans docker-compose.yml
ports:
  - "8001:8000"
```

## 📞 Support

Pour toute question ou problème, consultez la documentation complète dans `/backend/README.md`

## 📄 Licence

Propriétaire - StockFlow Pro © 2025
