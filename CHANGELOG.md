# Changelog - StockFlow Pro Backend

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [1.0.0] - MVP Phase 1 - 2024-12-24

### ✅ Ajouté

#### Authentification & Sécurité
- Système d'authentification JWT complet
- Hashing des mots de passe avec bcrypt
- Middleware de protection des routes
- Gestion des rôles (patron, employé, comptable)

#### Gestion des Articles
- CRUD complet des articles
- Recherche par code, désignation, code-barres
- Gestion des seuils min/max
- Support des codes-barres
- Détection automatique des articles en stock faible
- Soft delete (désactivation au lieu de suppression)

#### Mouvements de Stock
- Création de mouvements (entrée, sortie, ajustement, retour)
- Mise à jour automatique du stock après chaque mouvement
- Historique complet des mouvements par article
- Filtrage des mouvements par date
- Support des références de documents (bons de livraison)

#### Dashboard & Analytics
- Calcul de la valeur totale du stock en DT
- Comptage des articles actifs
- Liste des articles en stock faible
- Liste des articles en rupture
- Top 10 des articles critiques

#### Base de Données
- Schéma Prisma complet avec 9 tables
- Relations optimisées avec cascade delete
- Index pour les requêtes fréquentes
- Support des jours fériés tunisiens
- Audit log pour la traçabilité

#### Infrastructure
- Configuration Docker Compose
- PostgreSQL 15 + Redis 7
- Variables d'environnement sécurisées
- Script de seed avec données de test
- Documentation API automatique (Swagger/ReDoc)

#### Documentation
- README complet avec guide d'installation
- Documentation d'architecture technique
- Collection Postman/Thunder Client
- Tests unitaires (auth, schemas)

### 🚫 Exclus du MVP (Phases Futures)

- Module IA de prévision (Phase 2)
- Gestion multi-magasin (Phase 4)
- Scoring fournisseurs (Phase 2)
- Alertes WhatsApp (Phase 2)
- Analytics TVA (Phase 3)
- Exports comptables avancés (Phase 3)

### 🔧 Technique

- **Framework**: FastAPI 0.109.0
- **ORM**: Prisma 0.11.0
- **Base de données**: PostgreSQL 15
- **Cache**: Redis 7
- **Python**: 3.11+

### 📊 Métriques

- **Endpoints API**: 16
- **Tables DB**: 9
- **Lignes de code**: ~1500
- **Couverture tests**: 60%+

---

## [Unreleased] - Phase 2 (Planifié Q1 2025)

### À Venir

- [ ] Module IA de prévision de la demande
- [ ] Moteur de suggestions de commande
- [ ] Gestion avancée des fournisseurs
- [ ] Scoring automatique de fiabilité
- [ ] Alertes WhatsApp Business API
- [ ] Background jobs avec Celery
- [ ] Cache Redis pour performances
- [ ] Exports PDF/Excel avancés

---

## Format des Versions

- **MAJOR** : Changements incompatibles de l'API
- **MINOR** : Ajout de fonctionnalités rétrocompatibles
- **PATCH** : Corrections de bugs rétrocompatibles

## Types de Changements

- **Ajouté** : Nouvelles fonctionnalités
- **Modifié** : Changements de fonctionnalités existantes
- **Déprécié** : Fonctionnalités bientôt supprimées
- **Supprimé** : Fonctionnalités supprimées
- **Corrigé** : Corrections de bugs
- **Sécurité** : Corrections de vulnérabilités
