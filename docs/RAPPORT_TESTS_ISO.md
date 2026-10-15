# Rapport de tests et contribution aux contrôles ISO

Projet : AuditHub, interface React et API Django de gestion documentaire des tests d’intrusion. Dernière validation : 15 octobre 2026. Périmètre : code applicatif, base temporaire SQLite, client HTTP Django et navigateur Chrome headless. Aucune cible externe n’a été scannée.

## État de la validation

Validation exécutée le 15 octobre 2026 sous Windows, Python 3.13, Django 5.2.17 et SQLite : **33 tests backend réussis sur 33** et **3 parcours navigateur réussis sur 3**. React 19.3.0, esbuild 0.28.2, Playwright 1.63.0. Les tests navigateur utilisent une base temporaire séparée et ne modifient pas les comptes ni les missions de la base métier.

| Commande exécutée | Résultat observé |
|---|---|
| `manage.py migrate` | Toutes les migrations appliquées |
| `manage.py test --verbosity 1` | 33 tests, OK |
| `npm --prefix frontend run build` | Bundle React JS/CSS compilé |
| `npm --prefix frontend test` | 3 parcours Chrome headless, OK |
| `manage.py check` | Aucun problème identifié |
| `manage.py makemigrations --check --dry-run` | Aucun changement détecté |
| `manage.py check --deploy` | Aucun problème identifié, mode production et clé temporaire de validation |
| `python -m pip check` | Aucune incompatibilité de dépendances détectée |

`pip check` vérifie la cohérence des dépendances, pas l’absence de vulnérabilités. `check --deploy` vérifie les paramètres Django, pas l’infrastructure HTTPS réelle. Les parcours React sont testés dans Chrome et des captures desktop/mobile ont été générées. Ces tests ne constituent pas un test d’intrusion indépendant ni une certification.

## Plan de tests

| Domaine | Scénarios couverts dans `portal/tests.py` | Critère d’acceptation |
|---|---|---|
| Authentification | Accès anonyme, connexion, déconnexion, mot de passe faible et hachage | API 401, redirection React vers connexion, secret non stocké en clair |
| RBAC | Auditeur en écriture, utilisateur sans rôle, journal global | Refus 403, aucun changement métier |
| Cloisonnement | Consultation/export/saisie d’une mission non affectée | Refus 404 |
| Autorisation | Cible hors périmètre, cible contenant une commande, date future, mission expirée ou clôturée | Aucun résultat ajouté |
| Navigateur | CSRF sur connexion et changement d’état, XSS stockée, en-têtes, mutations GET | Refus ou échappement, CSP et no-store |
| Traçabilité | Empreinte, événement de saisie, export de rapport | Preuve et trace retrouvées |
| Corrections | Résolution sans puis avec preuve de re-test | Preuve exigée |
| Disponibilité des parcours | Rendu des principales pages autorisées | HTTP 200 |
| Force brute | Cinq échecs puis une sixième tentative | HTTP 429 |
| Session React | Jeton CSRF récupéré puis renouvelé après connexion, POST authentifié et déconnexion | Session utilisable sans exposer le cookie HttpOnly |
| Contrat API | Schémas de formulaire, erreurs JSON, liens directs, création avec membres multiples | Aucune fuite de mot de passe, validations 422 |

Les trois tests de `frontend/tests/workflows.spec.js` vérifient :

1. Connexion, création d’une mission, rejet d’une cible hors périmètre, saisie de preuve contenant du texte HTML, absence d’exécution XSS, résolution avec preuve obligatoire, téléchargement JSON, rechargement direct, clôture, filtre du journal, déconnexion et accès auditeur en lecture.
2. Création de compte avec rejet d’un mot de passe faible, quatre outils visibles, matrice ISO, historique de navigation, affichage mobile de 390 px sans débordement horizontal.
3. Refus d’accès d’un pentesteur à l’administration et retour à la connexion après suppression des cookies de session.

## Matrice ISO — analyse de contribution, à valider par l’auditeur

| Contrôle du sujet | Dispositif livré | Preuve à collecter | Écart / action restante |
|---|---|---|---|
| A.8.8 — Gestion des vulnérabilités techniques | Registre par mission : cible, outil/version, sévérité, correction, responsable, échéance, re-test | Rapport JSON, résultats originaux, suivi daté | Ajouter veille, inventaire complet, SLA, gestion des exceptions et revue des risques |
| A.8.25 — Cycle de vie de développement sécurisé | Rôles, validation, sessions, CSRF, échappement, configuration de production, tests | Code revu, résultats CI, modèle de menaces, décision de livraison | Mettre en place revue indépendante, SAST/SCA, verrou de dépendances, séparation des environnements |
| A.8.29 — Tests de sécurité en développement et acceptation | Méthode, date, version, preuve, empreinte et re-test documentés | Plan de recette signé, rapport exporté, résultats des tests applicatifs | Définir critères de sortie, tester l’environnement cible et faire approuver la recette |

## Réserves

- Intégration des outils documentaire uniquement ; aucun connecteur d’exécution ni import natif de rapport.
- Journal modifiable au niveau DB par les administrateurs système ; l’inviolabilité et la rétention ne sont pas garanties par l’application seule.
- Empreinte SHA-256 non signée : détection de changement seulement si comparée à une référence conservée indépendamment.
- Pas de MFA, récupération autonome de compte, chiffrement applicatif de la base ni validation indépendante des preuves saisies.
- Charge, concurrence, proxy TLS, sauvegarde/restauration, scan DAST et revue de sécurité indépendante à exécuter avant production.
- Aucun procès-verbal de recette organisationnelle ni déclaration d’applicabilité ISO n’a été signé dans le cadre de ce livrable.

## Références

Les numéros et intitulés de contrôles proviennent du sujet fourni. La matrice représente l’analyse du projet, pas une reproduction normative. [ISO/IEC 27001:2022](https://www.iso.org/standard/27001) définit le cadre du SMSI ; [ISO/IEC 27002:2022](https://www.iso.org/standard/75652.html) fournit les recommandations de contrôle. La validation normative complète demande les textes sous licence et les éléments organisationnels. Les protections de base suivent la [documentation Django](https://docs.djangoproject.com/en/5.2/topics/security/).
