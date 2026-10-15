# AuditHub — Projet 4

Interface web **React + API Django** en français pour gérer des missions de tests d’intrusion, centraliser les résultats Nmap, Metasploit, Burp Suite et OWASP ZAP, et préparer les preuves d’un audit technique.

**Périmètre livré : gestion documentaire fonctionnelle.** Les outils sont exécutés séparément dans un laboratoire autorisé. L’application n’installe ni ne lance ces outils et ne simule pas de résultats. Les preuves sont saisies en texte, sans import automatique de fichiers. Aucun compte ni mot de passe prédéfini.

## Démarrage local (PowerShell)

Prérequis : Python 3.12 ou 3.13 installé. Depuis ce dossier :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:AUDIT_DEV = '1'
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Ouvrir http://127.0.0.1:8000. Le superutilisateur accède à l’interface comme administrateur. Créer les comptes dans **Utilisateurs**, puis une mission dans **Missions d’audit**. Le multi-choix des habilitations utilise Ctrl/Cmd + clic.

Un interpréteur embarqué de vérification peut être présent dans `.runtime/python/python.exe` ; il est local et ignoré par Git. Il peut remplacer `python` pour les commandes `manage.py`. Utiliser une installation Python maintenue pour le déploiement.

## Fonctionnalités

- Authentification Django, mots de passe hachés, sessions de 30 minutes d’inactivité, limitation des tentatives par compte et IP.
- Trois rôles, contrôles serveur et accès aux missions par habilitation.
- Autorisation écrite référencée, période, IP/CIDR et membres définis par l’administrateur.
- Résultats datés avec version de l’outil, méthode, preuve textuelle et SHA-256.
- Sévérité, responsable, échéance, correction, suivi et preuve obligatoire pour la résolution.
- Export JSON de mission ; export global des événements réservé à l’administrateur.
- Interface responsive entièrement React, navigation sans rechargement, validation affichée dans les formulaires, chargement et gestion des erreurs. JavaScript requis ; aucune ressource CDN.

## Frontend React

Tout le frontend est dans `frontend/src/` : `main.jsx` pour les écrans et la navigation, `components.jsx` pour les composants réutilisables, `api.js` pour les appels JSON, `style.css` pour le style. `templates/app.html` n’est qu’une coque HTML qui charge le bundle React ; les anciens templates métier ont été supprimés.

Le bundle compilé est fourni dans `static/react/`. **Le démarrage Django ci-dessus suffit pour utiliser l’application**, sans serveur Node supplémentaire. Après une modification du frontend, reconstruire le bundle avec Node.js 22+ et npm :

```powershell
cd frontend
npm ci
npm run build
cd ..
```

Pour développer : `npm run dev` surveille les fichiers et recompile ; recharger le navigateur après une modification. Aucun hot reload ni second serveur web n’est nécessaire. Une distribution Node locale de validation est disponible sous `.runtime/node/node-v22.16.0-win-x64/` sur cette machine :

```powershell
$env:PATH = (Resolve-Path .runtime/node/node-v22.16.0-win-x64).Path + ';' + $env:PATH
npm.cmd --prefix frontend run build
```

L’API utilise `/api/`, les pages React conservent leurs URLs (`/missions/`, `/outils/`, etc.). Sessions Django en cookie HttpOnly, jeton CSRF récupéré via `/api/session/`, aucun jeton d’accès dans localStorage. Les formulaires React sont construits à partir d’un schéma de champs JSON ; les règles métier et permissions restent validées côté serveur.

## Vérification

```powershell
$env:AUDIT_DEV = '1'
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
npm --prefix frontend run build
npm --prefix frontend test
```

Le pipeline `.github/workflows/ci.yml` exécute ces contrôles à chaque push et pull request. `requirements-lock.txt` contient les versions Python validées ensemble.

Tests navigateur (Chrome installé) : `npm --prefix frontend test`. Ils lancent un serveur Django isolé sur le port 8765 avec une base temporaire ; les comptes de test ne sont jamais créés dans la base de travail. Définir `AUDIT_PYTHON` avec le chemin de Python si nécessaire, et `PLAYWRIGHT_CHANNEL=chromium` pour utiliser un Chromium installé via Playwright.

Validation actuelle : 33 tests Django et 3 parcours navigateur (création de mission, preuve, historique de re-test, export, RBAC, utilisateurs et affichage mobile). Voir le rapport pour les résultats détaillés.

Voir [le rapport de tests et la matrice ISO](docs/RAPPORT_TESTS_ISO.md), [le guide auditeur](docs/GUIDE_AUDITEUR.md) et [l’architecture et le déploiement](docs/ARCHITECTURE.md).

Les protections natives sont fondées sur la [documentation de sécurité Django](https://docs.djangoproject.com/en/5.2/topics/security/). La branche 5.2 LTS est sélectionnée selon la [table de support officielle](https://www.djangoproject.com/download/). Revoir les versions et produire un verrou de dépendances validé avant chaque mise en production.

## Positionnement ISO

La matrice utilise les contrôles A.8.8, A.8.25 et A.8.29 demandés dans le sujet. Les éléments techniques livrés contribuent à leur mise en œuvre. La conformité dépend de l’ensemble du SMSI et des preuves organisationnelles, comme le précise la [présentation officielle ISO/IEC 27001](https://www.iso.org/standard/27001). Les recommandations de mise en œuvre relèvent aussi d’[ISO/IEC 27002:2022](https://www.iso.org/standard/75652.html). Les textes normatifs complets ne sont pas reproduits ; valider la matrice avec les exemplaires sous licence de l’organisation.
