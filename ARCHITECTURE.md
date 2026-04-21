# Diagrammes d'Architecture & Choix Techniques
## Système de Monitoring Distribué

---

## 1. Diagramme C4 — Vue Contexte

```
╔══════════════════════════════════════════════════════════════╗
║              SYSTÈME DE MONITORING DISTRIBUÉ                 ║
║                                                              ║
║  ┌─────────────┐    métriques    ┌────────────────────────┐  ║
║  │  Opérateur  │────────────────▶│   Système Monitoring   │  ║
║  │  (DevOps)   │◀────dashboards──│   (ce système)         │  ║
║  └─────────────┘                 └────────────────────────┘  ║
║                                           │                  ║
║                               ┌───────────▼──────────┐      ║
║                               │   Machines surveillées│      ║
║                               │   (serveurs, VMs...)  │      ║
║                               └──────────────────────┘      ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 2. Diagramme Architecture Globale (Blocs)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        COUCHE COLLECTE                              │
│                                                                     │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐           │
│   │   Agent 1   │    │   Agent 2   │    │   Agent N   │           │
│   │  CPU/RAM/   │    │  CPU/RAM/   │    │  CPU/RAM/   │           │
│   │  Disque     │    │  Disque     │    │  Disque     │           │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘           │
└──────────┼─────────────────┼─────────────────┼───────────────────┘
           │  JSON payload    │                  │
           └──────────────────▼──────────────────┘
                     ┌─────────────────┐
                     │    COUCHE       │
                     │   MESSAGING     │
                     │                 │
                     │   RabbitMQ      │
                     │  Queue:metrics  │
                     │  (durable=True) │
                     └────────┬────────┘
                              │ consume async
                     ┌────────▼────────┐
                     │    COUCHE       │
                     │   TRAITEMENT    │
                     │                 │
                     │    Consumer     │
                     │  (Python async) │
                     │  alert_detector │
                     └────────┬────────┘
                              │ INSERT
               ┌──────────────▼──────────────┐
               │       COUCHE DONNÉES         │
               │                              │
               │         PostgreSQL           │
               │   nodes | metrics | alerts   │
               └──────────────┬──────────────┘
                              │ SELECT
               ┌──────────────▼──────────────┐
               │        COUCHE API            │
               │                              │
               │       FastAPI Server         │
               │    JWT Auth | REST API       │
               │    /metrics | /nodes         │
               │    /alerts  | /health        │
               └──────────┬───────────────────┘
                    ┌──────┴───────┐
          ┌─────────▼────┐  ┌──────▼──────────┐
          │  Prometheus  │  │  Clients HTTP    │
          │  (scraping)  │  │  Postman/Browser │
          └─────────┬────┘  └─────────────────┘
                    │
          ┌─────────▼────┐
          │   Grafana    │
          │  Dashboards  │
          └──────────────┘
```

---

## 3. Diagramme de Flux de Données

```
AGENT                  RABBITMQ            CONSUMER              DATABASE
  │                       │                    │                     │
  │─── collect() ────────▶│                    │                     │
  │    {                  │                    │                     │
  │     node_id: 1,       │                    │                     │
  │     cpu: 45.2,        │                    │                     │
  │     memory: 62.1,     │                    │                     │
  │     disk: 23.0,       │                    │                     │
  │     timestamp: ...    │                    │                     │
  │    }                  │                    │                     │
  │                       │─── message ───────▶│                     │
  │                       │                    │── SELECT node ──────▶│
  │                       │                    │◀─ node (ou None) ───│
  │                       │                    │                     │
  │                       │                    │ [si node inexistant]│
  │                       │                    │── INSERT node ──────▶│
  │                       │                    │                     │
  │                       │                    │── INSERT metric ────▶│
  │                       │                    │                     │
  │                       │                    │── detect_alerts() ──│
  │                       │                    │   [si seuil dépassé]│
  │                       │                    │── INSERT alert ─────▶│
  │                       │                    │                     │
  │                       │                    │── COMMIT ───────────▶│
  │                       │── ack message ────▶│                     │
  │                       │                    │                     │

   10s plus tard...
  │─── collect() ────────▶│  (cycle recommence)
```

---

## 4. Diagramme de Séquence — Authentification JWT

```
Client          FastAPI          Database        JWT
  │                │                 │             │
  │── POST /login ▶│                 │             │
  │   {user, pwd} │                 │             │
  │               │── SELECT user ──▶│             │
  │               │◀─ user record ──│             │
  │               │── verify_pwd() ─────────────▶ │
  │               │◀─ True/False ──────────────── │
  │               │── create_token() ───────────▶ │
  │               │◀─ JWT token ───────────────── │
  │◀─ {token} ────│                 │             │
  │               │                 │             │
  │── GET /metrics│                 │             │
  │   Bearer: JWT ▶                 │             │
  │               │── decode_jwt() ─────────────▶ │
  │               │◀─ {sub, role} ─────────────── │
  │               │── SELECT data ──▶│             │
  │               │◀─ metrics ──────│             │
  │◀─ [metrics] ──│                 │             │
```

---

## 5. Modèle de Données

```
┌─────────────────────┐      ┌──────────────────────┐
│        nodes        │      │       metrics        │
├─────────────────────┤      ├──────────────────────┤
│ id          INTEGER │      │ id          INTEGER   │
│ external_id VARCHAR │◀─┐   │ node_id     INTEGER  │──┐
│ name        VARCHAR │  │   │ timestamp   DATETIME  │  │
│ status      VARCHAR │  │   │ cpu_percent FLOAT     │  │
│ registered_at DATETIME│  │   │ memory_%    FLOAT     │  │
│ last_seen   DATETIME │  │   │ disk_%      FLOAT     │  │
└─────────────────────┘  │   └──────────────────────┘  │
                          │                              │
                          └──────────────────────────────┘
                          │
┌─────────────────────┐  │   ┌──────────────────────┐
│        users        │  │   │        alerts        │
├─────────────────────┤  │   ├──────────────────────┤
│ id          INTEGER │  │   │ id          INTEGER   │
│ username    VARCHAR │  │   │ node_id     INTEGER  │──┘
│ hashed_pwd  VARCHAR │  │   │ metric_type VARCHAR   │
│ role        VARCHAR │  │   │ threshold   FLOAT     │
└─────────────────────┘  │   │ actual_value FLOAT    │
                          │   │ severity    VARCHAR   │
                          │   │ message     VARCHAR   │
                          │   │ created_at  DATETIME  │
                          │   │ acknowledged BOOLEAN  │
                          └──▶└──────────────────────┘
```

---

## 6. Choix Techniques Justifiés

### 6.1 FastAPI (vs Flask / Django)

| Critère | FastAPI | Flask | Django |
|---------|---------|-------|--------|
| Performance | ⭐⭐⭐⭐⭐ async natif | ⭐⭐⭐ sync | ⭐⭐⭐ sync |
| Documentation auto |  Swagger/OpenAPI |  manuel |  manuel |
| Validation données |  Pydantic intégré |  externe |  DRF |
| Courbe apprentissage | Moyenne | Faible | Élevée |
| Adapté monitoring |  | Possible | Overkill |

**Choix** : FastAPI pour ses performances async (idéal pour les SSE et requêtes concurrentes), la génération automatique de documentation Swagger, et la validation Pydantic intégrée.

---

### 6.2 RabbitMQ (vs Kafka / Redis Pub-Sub)

| Critère | RabbitMQ | Kafka | Redis |
|---------|----------|-------|-------|
| Complexité setup | Faible | Élevée | Très faible |
| Persistance messages | ✅ | ✅ | ❌ (optionnel) |
| Retry automatique | ✅ | ✅ | ❌ |
| Monitoring UI | ✅ | ❌ natif | ❌ |
| Volume messages | Moyen | Très élevé | Moyen |

**Choix** : RabbitMQ pour sa simplicité de déploiement, l'interface de management intégrée, et la garantie de livraison des messages (durable=True). Kafka serait disproportionné pour ce volume de métriques.

---

### 6.3 PostgreSQL (vs MySQL / SQLite / InfluxDB)

| Critère | PostgreSQL | MySQL | SQLite | InfluxDB |
|---------|------------|-------|--------|----------|
| Requêtes complexes | ✅ | ✅ | Limité | ❌ |
| Séries temporelles | Acceptable | Acceptable | ❌ | ⭐⭐⭐⭐⭐ |
| Transactions ACID | ✅ | ✅ | ✅ | Partiel |
| Docker officiel | ✅ | ✅ | N/A | ✅ |
| Compatibilité ORM | ✅ | ✅ | ✅ | ❌ SQLAlchemy |

**Choix** : PostgreSQL pour sa robustesse, compatibilité parfaite avec SQLAlchemy, et capacité à gérer les requêtes d'agrégation (min/max/avg). InfluxDB serait plus optimal pour les time-series mais aurait nécessité un ORM différent.

---

### 6.4 Prometheus + Grafana (vs ELK Stack / Datadog)

| Critère | Prometheus+Grafana | ELK Stack | Datadog |
|---------|-------------------|-----------|---------|
| Open source | ✅ | ✅ | ❌ |
| Coût | Gratuit | Gratuit | Payant |
| Setup | Simple | Complexe | Simple |
| Alerting | ✅ | ✅ | ✅ |
| Standard industrie | ✅ K8s | ✅ logs | ✅ SaaS |

**Choix** : Prometheus + Grafana est le standard industrie pour le monitoring d'infrastructure, gratuit, et parfaitement intégré avec Docker.

---

### 6.5 Architecture Microservices

Le projet est découpé en services indépendants :
- **server** : API REST + logique métier
- **consumer** : traitement asynchrone des messages
- **agent** : collecte légère déployable sur N machines

**Avantages** :
- Scalabilité indépendante (ex: multiplier les agents sans toucher au server)
- Résilience : un agent qui tombe n'affecte pas le server
- Déploiement indépendant de chaque composant

**Compromis** : Complexité réseau accrue, nécessite Docker Compose ou Kubernetes pour l'orchestration.
