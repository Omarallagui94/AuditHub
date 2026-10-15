# Architecture, exploitation et développement sécurisé

## Architecture

Navigateur React → API JSON Django `/api/` → SQLite. Toutes les pages et tous les formulaires sont rendus par React. Django conserve l’authentification, le RBAC, la validation des formulaires et l’ORM. Le seul template restant charge le bundle React compilé par esbuild. Les outils Nmap, Metasploit, Burp Suite et ZAP restent dans le laboratoire externe. Aucun secret d’outil, shell, connecteur RPC ou exécuteur de commande n’est exposé.

React et l’API sont servis sur la même origine. `/api/session/` retourne le profil public et un jeton CSRF masqué, renouvelé après connexion. Les requêtes POST envoient ce jeton dans `X-CSRFToken`. Les cookies de session restent HttpOnly. Aucune configuration CORS permissive et aucun secret en localStorage. Les endpoints répondent en JSON, avec statuts 401/403/404/409/422/429 adaptés. Les liens directs chargent la coque React puis les données autorisées.

`Mission` porte l’autorisation, la fenêtre et le périmètre ; `TestRecord` conserve les constats et corrections ; `AuditEvent` conserve les événements ; `LoginAttempt` maintient les fenêtres de limitation de connexion. Les écritures métier et leur événement sont regroupés dans une transaction.

SQLite convient à un prototype ou à une petite installation mono-instance. Valider le comportement concurrent et migrer vers PostgreSQL pour une charge multi-utilisateur importante. Le limiteur DB n’est pas un dispositif anti-DDoS. Planifier `python manage.py purge_login_attempts` et appliquer aussi un limiteur au reverse proxy. Plusieurs utilisateurs derrière une même IP partagent la limite réseau ; seules les authentifications échouées consomment ce quota.

## Menaces et protections

| Menace | Protection livrée | Limite |
|---|---|---|
| Accès anonyme / privilège indu | Authentification, rôle vérifié serveur, habilitation de mission | Pas de MFA / SSO |
| Accès direct à une autre mission | Querysets filtrés par membre avant lecture, écriture et export | Administrateur autorisé sur toutes les missions |
| CSRF / XSS | Middleware CSRF, échappement React, CSP limitée aux scripts de même origine sans inline/eval, cookies SameSite | Ne pas introduire de HTML brut dans React |
| Injection SQL / commande | ORM ; aucune commande système ni scan exécuté | Futurs connecteurs à auditer séparément |
| Force brute | Fenêtre 15 min : 5 tentatives par compte, 30 par IP | Un attaquant peut provoquer un blocage temporaire |
| Altération des preuves | Texte initial sans modification UI et empreinte SHA-256 | Une empreinte stockée avec la preuve ne garantit pas l’intégrité face à un administrateur DB |
| Effacement de traces | Aucun endpoint d’édition/suppression des événements | Base modifiable par l’administrateur système, stockage WORM externe nécessaire |
| Fuite d’exports | Authentification, périmètre et téléchargement JSON non exécutable | Protection des copies à la charge de l’organisation |

## Déploiement

Le mode local `AUDIT_DEV=1` désactive les cookies Secure, la redirection HTTPS et HSTS pour permettre le développement sur loopback. Ne pas exposer ce mode sur un réseau partagé.

Pour un déploiement :

1. Fournir `AUDIT_SECRET_KEY` aléatoire d’au moins 50 caractères par gestionnaire de secrets, retirer `AUDIT_DEV`, définir `AUDIT_HOSTS` sur les domaines exacts.
2. Compiler React avec `npm ci` puis `npm run build` dans `frontend/`. Terminer TLS sur un reverse proxy approuvé, servir les fichiers statiques après `python manage.py collectstatic --noinput`. Le serveur de production n’a pas besoin de Node. Les noms de bundle sont fixes : configurer la revalidation des fichiers `/static/react/app.js` et `app.css` (pas de cache immutable). Aucun traitement de fichiers téléversés n’est prévu.
3. Exécuter via Waitress, installé avec les dépendances : `waitress-serve --listen=127.0.0.1:8000 config.wsgi:application`. Pour TLS terminé au proxy, définir `AUDIT_TRUST_PROXY=1` et configurer **explicitement** Waitress avec `--trusted-proxy=127.0.0.1 --trusted-proxy-headers=x-forwarded-proto,x-forwarded-for` seulement si le proxy local remplace ces en-têtes et que le backend n’est pas exposé. Adapter l’adresse de confiance à l’architecture. Le paramètre configure aussi `SECURE_PROXY_SSL_HEADER`, évitant une boucle de redirection HTTPS.
4. Exécuter `python manage.py check --deploy`, les migrations et les tests avant la mise en service. Vérifier réellement TLS, redirections, cookies Secure, en-têtes et restauration de sauvegarde dans l’environnement cible.
5. Restreindre les ACL du dossier et de SQLite au compte de service. Chiffrer le disque et les sauvegardes, maintenir une copie testée. Définir une politique de conservation validée par l’organisation.
6. Exporter les journaux vers un stockage externe à accès et rétention contrôlés. Superviser échecs de connexion, refus d’accès, erreurs serveur et disponibilité. Le journal applicatif ne remplace pas les logs proxy/système.

Ce dépôt ne fournit pas de proxy TLS ni de service Windows prêt à installer. Les limites de taille des requêtes doivent être également appliquées au proxy. Éviter d’exposer des secrets dans les erreurs ou les journaux d’infrastructure.

## Cycle de développement (A.8.25)

Avant chaque livraison : formaliser les exigences, réviser les menaces, faire relire les modifications RBAC et données, exécuter les tests et les contrôles de dépendances, approuver la recette puis archiver versions et résultats. Séparer développement, recette et production ; aucune donnée de production dans les fixtures.

`requirements-lock.txt` fixe les versions Python validées ensemble et le frontend dispose de `package-lock.json` pour `npm ci`. Ajouter des empreintes de paquets et une nomenclature logicielle (SBOM) au processus de publication, examiner les vulnérabilités et tester les mises à jour. Cela ne remplace pas une revue de sécurité ni une analyse SAST complète.

## Extension vers l’exécution d’outils

Créer un service worker isolé du serveur web, des profils d’exécution autorisés, une file de tâches, des quotas et délais, un arrêt d’urgence, une validation de périmètre juste avant exécution et un filtrage réseau sortant. Passer des arguments structurés sans shell, cloisonner les secrets et journaliser lancement, annulation et résultat. Pour Burp/Metasploit, tenir compte des API et licences installées. Cette extension est hors du périmètre exécuté de cette première version.
