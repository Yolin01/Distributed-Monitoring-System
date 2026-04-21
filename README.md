
#  Distributed Monitoring System

> Plateforme de surveillance en temps réel basée sur FastAPI, RabbitMQ, PostgreSQL, Prometheus et Grafana — entièrement containerisée avec Docker.

[![CI/CD](https://github.com/Yolin01/Distributed-Monitoring-System/actions/workflows/ci.yml/badge.svg)](https://github.com/Yolin01/Distributed-Monitoring-System/actions)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://docker.com)
[![Tests](https://img.shields.io/badge/tests-16%20passed-brightgreen)](https://github.com/Yolin01/Distributed-Monitoring-System/actions)
[![Coverage](https://img.shields.io/badge/coverage-69%25-yellow)](https://github.com/Yolin01/Distributed-Monitoring-System/actions)

---

##  Table des matières

1. [Description](#description)
2. [Architecture](#architecture)
3. [Prérequis](#prérequis)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Lancement](#lancement)
7. [Utilisation](#utilisation)
8. [Structure du projet](#structure-du-projet)
9. [Tests](#tests)
10. [CI/CD Pipeline](#cicd-pipeline)
11. [Maintenance](#maintenance)

---

##  Description

Ce système permet de surveiller en temps réel les ressources système (CPU, RAM, Disque) de plusieurs machines distribuées. Les agents collectent les métriques et les envoient via RabbitMQ à un serveur central qui les stocke, les expose via API REST et déclenche des alertes automatiques selon des seuils configurables.

### Fonctionnalités principales

- **Collecte automatique** des métriques système toutes les 10 secondes
- **API REST sécurisée** avec authentification JWT
- **Alertes automatiques** selon seuils configurables (CPU, RAM, Disque)
- **Visualisation temps réel** via Grafana
- **Architecture résiliente** avec RabbitMQ (retry + reconnexion automatique)
- **Multi-agents** : surveiller N machines simultanément
- **CI/CD Pipeline** : tests automatiques et déploiement continu

---

##  Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AGENTS (N machines)                         │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │   Agent 1    │      │   Agent 2    │      │   Agent N    │  │
│  │  (psutil)    │      │  (psutil)    │      │  (psutil)    │  │
└──┴──────┬───────┴──────┴──────┬───────┴──────┴──────┬───────┘──┘
          │ JSON metrics         │                      │
          └──────────────────────▼──────────────────────┘
                         ┌───────────────┐
                         │   RabbitMQ    │
                         │  Queue:metrics│
                         │   Port 5672   │
                         └───────┬───────┘
                                 │ consume
                    ┌────────────▼─────────────┐
                    │        Consumer           │
                    │     (Python async)        │
                    └────────────┬─────────────┘
                                 │ INSERT
                    ┌────────────▼─────────────┐
                    │       PostgreSQL          │
                    │    Base de données        │
                    │       Port 5432           │
                    └────────────┬─────────────┘
                                 │ SELECT
                    ┌────────────▼─────────────┐
                    │     Server FastAPI        │
                    │    API REST + JWT         │
                    │       Port 8000           │
                    └────────────┬─────────────┘
                         ┌───────┴────────┐
              ┌──────────▼──────┐  ┌──────▼──────────┐
              │   Prometheus    │  │   Clients HTTP  │
              │  Port 9090      │  │  (Postman/Browser)│
              └──────────┬──────┘  └─────────────────┘
                         │
              ┌──────────▼──────┐
              │     Grafana     │
              │  Dashboards     │
              │   Port 3000     │
              └─────────────────┘
```

### Flux de données

```
Agent → [collecte psutil] → [JSON payload] → RabbitMQ queue "metrics"
     → Consumer [lit la queue] → [INSERT PostgreSQL]
     → Server FastAPI [SELECT PostgreSQL] → [REST API /metrics]
     → Prometheus [scrape /metrics] → Grafana [dashboard]
```

---

##  Stack technique

| Composant | Technologie | Version | Rôle |
|-----------|-------------|---------|------|
| API Backend | FastAPI | 0.111 | REST API + documentation Swagger |
| Base de données | PostgreSQL | 15 | Stockage persistant des métriques |
| Message broker | RabbitMQ | 3-management | File de messages asynchrone |
| Agent collecte | Python + psutil | 3.11 | Collecte métriques système |
| ORM | SQLAlchemy | 2.0 | Mapping objet-relationnel |
| Authentification | JWT + bcrypt | — | Sécurité API |
| Monitoring | Prometheus | latest | Collecte et stockage métriques |
| Visualisation | Grafana | latest | Dashboards temps réel |
| Containerisation | Docker Compose | v2 | Orchestration services |
| CI/CD | GitHub Actions | — | Tests et déploiement automatiques |

### Pourquoi ces choix ?

- **FastAPI** : performances élevées (async), documentation auto-générée, validation Pydantic
- **RabbitMQ** : découplage agent/serveur, persistance des messages, retry automatique
- **PostgreSQL** : fiabilité, requêtes complexes, support des séries temporelles
- **Prometheus + Grafana** : standard industrie pour l'observabilité

---

##  Prérequis

| Outil | Version minimale | Installation |
|-------|-----------------|--------------|
| Docker Desktop | 24.0+ | https://docker.com/get-started |
| Docker Compose | 2.0+ | Inclus avec Docker Desktop |
| Git | 2.0+ | https://git-scm.com |

> **Note Windows** : Activez WSL2 dans Docker Desktop pour de meilleures performances.

---

##  Installation

### 1. Cloner le projet

```bash
git clone https://github.com/Yolin01/Distributed-Monitoring-System.git
cd Distributed-Monitoring-System
```

### 2. Configurer l'environnement

```bash
# Copier le fichier exemple
cp .env.example .env

# Éditer avec vos valeurs (obligatoire en production)
notepad .env        # Windows
nano .env           # Linux/Mac
```

### 3. Variables obligatoires à modifier

```env
SECRET_KEY=changez-cette-valeur-minimum-32-caracteres
POSTGRES_PASSWORD=votre-mot-de-passe-fort
```

---

##  Configuration

### Fichier `.env` complet

```env
# ── Serveur ──────────────────────────────────────
ENV=development
SECRET_KEY=mon-secret-tres-long-32-caracteres-min
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ── Base de données ───────────────────────────────
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/monitoring
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changez-moi
POSTGRES_DB=monitoring

# ── RabbitMQ ──────────────────────────────────────
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
RABBITMQ_QUEUE=metrics

# ── Agent ─────────────────────────────────────────
AGENT_USERNAME=agent-node-01
SERVER_URL=http://server:8000
```

### Seuils d'alertes (`config/thresholds.yaml`)

```yaml
cpu:
  warning: 70    # Alerte warning si CPU > 70%
  critical: 90   # Alerte critique si CPU > 90%
memory:
  warning: 75
  critical: 90
disk:
  warning: 80
  critical: 95
```

---

##  Lancement

### Démarrage complet

```bash
# Build et démarrage de tous les services
docker compose up --build

# En arrière-plan (recommandé)
docker compose up --build -d
```

### Vérification du démarrage

```bash
docker compose ps
```

Résultat attendu — tous les services **Up** :

```
NAME                      STATUS          PORTS
monitoring-server-1       Up (healthy)    0.0.0.0:8000->8000/tcp
monitoring-consumer-1     Up
monitoring-agent-1        Up
monitoring-postgres-1     Up (healthy)    0.0.0.0:5432->5432/tcp
monitoring-rabbitmq-1     Up (healthy)    0.0.0.0:5672->5672/tcp
monitoring-prometheus-1   Up              0.0.0.0:9090->9090/tcp
monitoring-grafana-1      Up              0.0.0.0:3000->3000/tcp
```

### Arrêt

```bash
# Arrêt simple (données conservées)
docker compose down

# Arrêt + suppression des données
docker compose down -v
```

---

##  Utilisation

### Interfaces disponibles

| Service | URL | Identifiants |
|---------|-----|--------------|
| API Swagger | http://localhost:8000/docs | Token JWT |
| Health Check | http://localhost:8000/health | — |
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | — |
| RabbitMQ Management | http://localhost:15672 | guest / guest |

---

###  API REST

#### 1. Obtenir un token JWT

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Réponse :
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

#### 2. Utiliser le token

```bash
# Stocker le token
TOKEN="eyJhbGci..."

# Faire une requête authentifiée
curl http://localhost:8000/metrics/latest \
  -H "Authorization: Bearer $TOKEN"
```

#### 3. Endpoints principaux

```bash
# Health check (sans auth)
GET /health

# Dernières métriques de tous les nodes
GET /metrics/latest

# Métriques d'un node (60 dernières minutes)
GET /metrics/node/{id}?minutes=60

# Statistiques (min, max, moyenne)
GET /metrics/node/{id}/stats

# Stream temps réel (Server-Sent Events)
GET /metrics/live

# Liste des nodes
GET /nodes/

# Alertes déclenchées
GET /alerts/
```

---

###  Grafana — Configuration rapide

#### Ajouter PostgreSQL comme datasource

1. Connections → Data sources → Add data source
2. Choisir **PostgreSQL**
3. Host : `postgres:5432`
4. Database : `monitoring`, User : `postgres`
5. TLS/SSL Mode : `disable`
6. **Save & test**

#### Query CPU temps réel

```sql
SELECT
  timestamp AS "time",
  cpu_percent AS "CPU %",
  n.name AS "Node"
FROM metrics m
JOIN nodes n ON n.id = m.node_id
WHERE $__timeFilter(timestamp)
ORDER BY timestamp ASC
```

---

##  Structure du projet

```
Distributed-Monitoring-System/
│
├── .env                          # Variables d'environnement
├── .env.example                  # Template des variables
├── .dockerignore                 # Fichiers exclus du build Docker
├── docker-compose.yml            # Orchestration des services
│
├── .github/
│   └── workflows/
│       └── ci.yml                # Pipeline CI/CD GitHub Actions
│
├── config/
│   ├── settings.py               # Configuration Pydantic
│   ├── thresholds.yaml           # Seuils d'alertes configurables
│   └── __init__.py
│
├── observability/
│   └── prometheus.yml            # Configuration scraping Prometheus
│
├── scripts/
│   ├── seed_db.py                # Données de démonstration
│   └── generate_agent_token.py   # Génération token agent
│
├── src/
│   ├── agent/                    # Service agent de collecte
│   │   ├── agent.py              # Collecte psutil → RabbitMQ
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── server/                   # Service API + Consumer
│       ├── Dockerfile
│       ├── requirements.txt
│       └── app/
│           ├── main.py           # Point d'entrée FastAPI
│           ├── database.py       # Connexion SQLAlchemy
│           ├── models.py         # Modèles ORM
│           ├── schemas.py        # Schémas Pydantic
│           ├── security.py       # JWT + bcrypt
│           ├── init_data.py      # Initialisation admin
│           ├── routers/
│           │   ├── auth.py       # POST /auth/login
│           │   ├── metrics.py    # GET /metrics/*
│           │   ├── nodes.py      # GET/POST /nodes/*
│           │   └── alerts.py     # GET /alerts/*
│           └── services/
│               ├── rabbitmq_consumer.py  # Lecture queue → DB
│               └── alert_detector.py     # Détection seuils
│
└── tests/
    └── integration/
        └── test_api.py           # 16 tests pytest
```

---

##  Tests

### Lancer les tests

```bash
# Tous les tests avec verbosité
docker compose exec server pytest tests/ -v

# Avec rapport de couverture
docker compose exec server pytest tests/ -v --cov=app --cov-report=term-missing
```

### Tests disponibles (16 tests)

| Classe | Test | Description |
|--------|------|-------------|
| TestAuth | test_login_success | Login valide retourne token |
| TestAuth | test_login_wrong_password | Mauvais mdp → 401 |
| TestAuth | test_login_unknown_user | User inconnu → 401 |
| TestAuth | test_protected_route_without_token | Sans token → 401 |
| TestAuth | test_protected_route_with_token | Avec token → 200 |
| TestAuth | test_invalid_token | Token invalide → 401 |
| TestHealth | test_health_check | /health → {"status":"ok"} |
| TestHealth | test_root | / → 200 |
| TestMetrics | test_list_metrics | Liste métriques → 200 |
| TestMetrics | test_list_metrics_pagination | limit/offset fonctionnels |
| TestMetrics | test_latest_metrics | /latest retourne liste |
| TestMetrics | test_node_metrics | /node/{id} → 200 |
| TestMetrics | test_node_stats | /node/{id}/stats → stats |
| TestMetrics | test_metrics_structure | Champs attendus présents |
| TestNodes | test_list_nodes | Liste nodes → 200 |
| TestNodes | test_node_structure | Champs node corrects |

---

##  CI/CD Pipeline

Ce projet utilise **GitHub Actions** pour l'intégration continue :

### Pipeline déclenché sur :
- `push` sur `main` et `develop`
- `pull_request` sur `main`

### Jobs exécutés :

| Job | Description |
|-----|-------------|
|  Tests | Exécute les 16 tests avec PostgreSQL et RabbitMQ |
|  Lint | Vérifie la qualité du code (flake8, black, isort) |
|  Build | Construit les images Docker |
|  Push | Publie les images sur GitHub Container Registry |
|  Deploy | Déploie automatiquement sur le serveur (main uniquement) |

### Badges de statut

```markdown
[![CI/CD](https://github.com/Yolin01/Distributed-Monitoring-System/actions/workflows/ci.yml/badge.svg)](https://github.com/Yolin01/Distributed-Monitoring-System/actions)
[![Tests](https://img.shields.io/badge/tests-16%20passed-brightgreen)](https://github.com/Yolin01/Distributed-Monitoring-System/actions)
[![Coverage](https://img.shields.io/badge/coverage-69%25-yellow)](https://github.com/Yolin01/Distributed-Monitoring-System/actions)
```

---

##  Maintenance

### Voir les logs

```bash
docker compose logs -f              # Tous les services
docker compose logs -f server       # Serveur API
docker compose logs -f consumer     # Consumer RabbitMQ
docker compose logs -f agent        # Agent collecte
```

### Backup de la base de données

```bash
docker compose exec postgres pg_dump \
  -U postgres monitoring \
  > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Mise à jour

```bash
git pull origin main
docker compose down
docker compose up --build -d
```

### Rollback

```bash
git log --oneline -5              # Voir les versions
git checkout <commit-hash>        # Revenir à une version
docker compose up --build -d      # Redémarrer
```

---

##  Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Fork le projet
2. Créez une branche (`git checkout -b feature/amazing-feature`)
3. Committez vos changements (`git commit -m 'Add amazing feature'`)
4. Pushez (`git push origin feature/amazing-feature`)
5. Ouvrez une Pull Request

---

##  Licence

MIT License — voir [LICENSE](LICENSE) pour plus de détails.

---

##  Auteur

**Projet réalisé dans le cadre du module Systèmes Répartis et Middleware**

- GitHub : [Yolin01](https://github.com/Yolin01)
- Projet : [Distributed Monitoring System](https://github.com/Yolin01/Distributed-Monitoring-System)

---

##  Remerciements

- FastAPI pour la documentation auto-générée
- RabbitMQ pour la robustesse du message broker
- Grafana pour les dashboards temps réel
- Docker pour la containerisation

---

##  Contact

Pour toute question concernant ce projet, merci d'ouvrir une **issue** sur GitHub.