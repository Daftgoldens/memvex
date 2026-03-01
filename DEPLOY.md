# 🚀 Déploiement sur Railway

## Pourquoi Railway ?
- Postgres + pgvector inclus nativement
- Déploiement depuis GitHub en 1 clic
- Free tier : 5$ de crédit/mois (largement suffisant pour les démos)
- URL publique automatique (ex: `agent-memory-layer.up.railway.app`)

---

## Étape 1 — Préparer le repo GitHub

```bash
cd agent-memory-layer

# Init git si pas encore fait
git init
git add .
git commit -m "feat: initial Agent Memory Layer POC"

# Créer un repo sur github.com puis :
git remote add origin https://github.com/VOTRE_USERNAME/agent-memory-layer.git
git push -u origin main
```

---

## Étape 2 — Créer le projet Railway

1. Aller sur **railway.app** → "Start a New Project"
2. Choisir **"Deploy from GitHub repo"**
3. Sélectionner votre repo `agent-memory-layer`
4. Railway détecte automatiquement le Dockerfile ✅

---

## Étape 3 — Ajouter PostgreSQL + pgvector

1. Dans votre projet Railway → **"+ New"** → **"Database"** → **"PostgreSQL"**
2. Railway crée automatiquement la variable `DATABASE_URL`
3. ⚠️ Railway utilise `postgresql://` — il faut le remplacer par `postgresql+asyncpg://`
   → Dans "Variables" de votre service API, ajoutez :
   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   ```
   Railway injecte automatiquement la bonne URL.

---

## Étape 4 — Variables d'environnement

Dans Railway → votre service API → onglet **"Variables"** :

| Variable | Valeur |
|---|---|
| `OPENAI_API_KEY` | `sk-votre-clé` |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (Railway le remplace automatiquement) |

---

## Étape 5 — Fixer l'URL pour asyncpg

Railway injecte `postgresql://` mais SQLAlchemy async a besoin de `postgresql+asyncpg://`.
Le fichier `railway.toml` ci-dessous gère ça automatiquement via une variable de substitution.

---

## Résultat

Votre API sera live sur :
```
https://agent-memory-layer-production.up.railway.app
```

Testez :
```bash
curl https://VOTRE-URL.up.railway.app/health
```

---

## Commandes utiles Railway CLI (optionnel)

```bash
# Installer Railway CLI
npm install -g @railway/cli

# Login
railway login

# Voir les logs en temps réel
railway logs

# Ouvrir le dashboard
railway open
```
