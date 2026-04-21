# Guide Utilisateur & Procédures de Maintenance
## Système de Monitoring Distribué

---

## PARTIE 1 — Guide Utilisateur

### 1.1 Démarrage rapide

```bash
# 1. Cloner et configurer
git clone https://github.com/votre-repo/monitoring-distribue.git
cd monitoring-distribue
cp .env.example .env

# 2. Démarrer
docker compose up --build -d

# 3. Vérifier (attendre 30 secondes)
docker compose ps

# 4. Ouvrir l'API
# http://localhost:8000/docs
```

---

### 1.2 Accès aux interfaces

#### API Swagger (http://localhost:8000/docs)

1. Ouvrez http://localhost:8000/docs dans votre navigateur
2. Cliquez **POST /auth/login** → **Try it out**
3. Entrez `username: admin` et `password: admin`
4. Copiez le `access_token` de la réponse
5. Cliquez **Authorize**  en haut de la page
6. Collez le token → **Authorize**
7. Tous les endpoints sont maintenant accessibles

#### Grafana (http://localhost:3000)

1. Login : `admin` / `admin` (changer en production)
2. Changer le mot de passe au premier login
3. Aller dans **Connections → Data sources** pour configurer PostgreSQL

#### RabbitMQ Management (http://localhost:15672)

1. Login : `guest` / `guest`
2. Onglet **Queues** : voir les messages en attente
3. Onglet **Overview** : surveiller le débit

---

### 1.3 Utilisation de l'API

#### Obtenir un token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"
```

```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

#### Exemples de requêtes

```bash
TOKEN="eyJhbGci..."

# Voir les nodes actifs
curl http://localhost:8000/nodes/ \
  -H "Authorization: Bearer $TOKEN"

# Dernières métriques de chaque node
curl http://localhost:8000/metrics/latest \
  -H "Authorization: Bearer $TOKEN"

# Stats CPU/RAM du node 1 (1 heure)
curl "http://localhost:8000/metrics/node/1/stats?minutes=60" \
  -H "Authorization: Bearer $TOKEN"

# Stream temps réel
curl http://localhost:8000/metrics/live \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: text/event-stream"
```

---

### 1.4 Comprendre les alertes

Les alertes sont générées automatiquement quand les seuils sont dépassés.

| Niveau | CPU | RAM | Disque |
|--------|-----|-----|--------|
| Warning | > 70% | > 75% | > 80% |
| Critical | > 90% | > 90% | > 95% |

Modifier les seuils dans `config/thresholds.yaml` puis redémarrer le consumer :
```bash
docker compose restart consumer
```

---

### 1.5 Ajouter un nouvel agent

Sur la machine à surveiller :

1. Copiez `src/agent/agent.py` et `src/agent/requirements.txt`
2. Installez les dépendances : `pip install -r requirements.txt`
3. Configurez les variables d'environnement :
```bash
export RABBITMQ_URL=amqp://guest:guest@IP_SERVEUR:5672/
export RABBITMQ_QUEUE=metrics
python agent.py
```

Ou via Docker :
```bash
docker run -e RABBITMQ_URL=amqp://guest:guest@IP_SERVEUR:5672/ \
  monitoring-agent:latest
```

---

## PARTIE 2 — Procédures de Maintenance

### 2.1 Vérification quotidienne

```bash
# État des services
docker compose ps

# Espace disque
docker system df

# Vérifier les métriques récentes (< 5min)
docker compose exec postgres psql -U postgres -d monitoring -c "
  SELECT COUNT(*), MAX(timestamp)
  FROM metrics
  WHERE timestamp > NOW() - INTERVAL '5 minutes';
"

# Vérifier les alertes critiques
docker compose exec postgres psql -U postgres -d monitoring -c "
  SELECT severity, COUNT(*)
  FROM alerts
  WHERE created_at > NOW() - INTERVAL '24 hours'
  GROUP BY severity;
"
```

---

### 2.2 Backup de la base de données

#### Backup manuel

```bash
# Backup complet avec timestamp
docker compose exec postgres pg_dump \
  -U postgres \
  --format=custom \
  monitoring \
  > backup_$(date +%Y%m%d_%H%M%S).dump

# Vérifier la taille
ls -lh backup_*.dump
```

#### Backup automatique (crontab Linux)

```bash
# Editer crontab
crontab -e

# Backup quotidien à 2h du matin
0 2 * * * cd /opt/monitoring && docker compose exec -T postgres pg_dump \
  -U postgres monitoring \
  > backups/backup_$(date +\%Y\%m\%d).sql

# Garder 30 jours de backups
0 3 * * * find /opt/monitoring/backups -name "backup_*.sql" -mtime +30 -delete
```

---

### 2.3 Restauration d'un backup

```bash
# 1. Arrêter l'application
docker compose stop server consumer agent

# 2. Supprimer les données actuelles (optionnel)
docker compose exec postgres psql -U postgres -c "DROP DATABASE monitoring;"
docker compose exec postgres psql -U postgres -c "CREATE DATABASE monitoring;"

# 3. Restaurer
docker compose exec -T postgres psql -U postgres monitoring < backup_20240101.sql

# OU avec format custom
docker compose exec -T postgres pg_restore \
  -U postgres \
  -d monitoring \
  backup_20240101.dump

# 4. Redémarrer
docker compose start server consumer agent

# 5. Vérifier
docker compose logs server --tail 10
```

---

### 2.4 Nettoyage des données anciennes

```bash
# Voir l'espace utilisé par table
docker compose exec postgres psql -U postgres -d monitoring -c "
  SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size('public.'||tablename)) AS size,
    COUNT(*) AS rows
  FROM pg_tables t
  JOIN information_schema.tables i
    ON i.table_name = t.tablename
  WHERE t.schemaname = 'public'
  GROUP BY tablename;
"

# Supprimer métriques de plus de 30 jours
docker compose exec postgres psql -U postgres -d monitoring -c "
  DELETE FROM metrics
  WHERE timestamp < NOW() - INTERVAL '30 days';
  VACUUM ANALYZE metrics;
"

# Supprimer alertes acquittées de plus de 7 jours
docker compose exec postgres psql -U postgres -d monitoring -c "
  DELETE FROM alerts
  WHERE acknowledged = true
  AND created_at < NOW() - INTERVAL '7 days';
"
```

---

### 2.5 Mise à jour du système

```bash
# 1. Backup préventif
docker compose exec postgres pg_dump \
  -U postgres monitoring > backup_avant_maj_$(date +%Y%m%d).sql

# 2. Récupérer les sources
git fetch origin
git log --oneline origin/main -5  # Voir les changements

# 3. Tester d'abord en local (optionnel)
git stash
git checkout origin/main -- .

# 4. Appliquer et redémarrer
docker compose down
docker compose up --build -d

# 5. Vérifier
docker compose ps
curl http://localhost:8000/health
docker compose logs server --tail 20
```

---

## PARTIE 3 — Procédures de Rollback

### 3.1 Rollback rapide (sans perte de données)

```bash
# Voir les 5 dernières versions
git log --oneline -5

# Revenir à la version précédente
git checkout HEAD~1

# Reconstruire et redémarrer
docker compose down
docker compose up --build -d

# Vérifier
docker compose ps
```

### 3.2 Rollback complet (avec restauration DB)

À utiliser si la mise à jour a modifié le schéma de base de données.

```bash
# 1. Arrêter tous les services
docker compose down

# 2. Revenir au code de la version précédente
git checkout <commit-hash>

# 3. Supprimer le volume PostgreSQL (ATTENTION : perte des données récentes)
docker volume rm monitoring_pgdata

# 4. Redémarrer (DB recréée vide)
docker compose up --build -d

# 5. Attendre que PostgreSQL soit prêt
sleep 10

# 6. Restaurer le backup pré-mise à jour
docker compose exec -T postgres psql \
  -U postgres monitoring \
  < backup_avant_maj_20240101.sql

echo "Rollback terminé"
```

### 3.3 Rollback d'urgence (réinitialisation totale)

 **Toutes les données seront perdues.**

```bash
# Arrêter et tout supprimer
docker compose down -v
docker system prune -f

# Revenir à la dernière version stable connue
git checkout main

# Redémarrer proprement
docker compose up --build -d

echo " Système réinitialisé — données perdues"
```

---

## PARTIE 4 — Dépannage

### Problème : Le server ne démarre pas

```bash
# Voir l'erreur précise
docker compose logs server --tail 50

# Erreurs communes :
# - ModuleNotFoundError → vérifier PYTHONPATH et volumes
# - SyntaxError → erreur dans le code Python
# - Connection refused postgres → PostgreSQL pas encore prêt
```

### Problème : L'agent ne s'envoie pas de métriques

```bash
# Test de connectivité
docker compose exec agent python -c \
  "import socket; s=socket.socket(); s.connect(('rabbitmq',5672)); print('OK')"

# Voir les tentatives de connexion
docker compose logs agent --tail 20

# Redémarrer l'agent
docker compose restart agent
```

### Problème : Pas de données dans Grafana

```bash
# 1. Vérifier que les métriques arrivent
docker compose exec postgres psql -U postgres -d monitoring -c \
  "SELECT COUNT(*), MAX(timestamp) FROM metrics;"

# 2. Vérifier le consumer
docker compose logs consumer --tail 20

# 3. Vérifier la datasource Grafana
# Grafana → Connections → Data sources → Test
```

### Problème : Mémoire insuffisante

```bash
# Voir l'utilisation
docker stats --no-stream

# Nettoyer les ressources Docker inutilisées
docker system prune -f
docker volume prune -f

# Réduire la rétention Prometheus
# Dans docker-compose.yml, modifier :
# --storage.tsdb.retention.time=7d  (au lieu de 15d)
```
