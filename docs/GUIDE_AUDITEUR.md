# Guide d’utilisation pour auditeurs

L’interface est une application React : JavaScript doit être activé. Les URLs et les rôles restent identiques ; les formulaires affichent les erreurs de validation sans perdre les valeurs saisies. Le serveur Django fournit les données et applique les permissions. Une session expirée renvoie à l’écran de connexion. Les exports JSON sont téléchargés par le navigateur.

## Rôles et habilitations

| Action | Administrateur | Pentesteur | Auditeur |
|---|---|---|---|
| Consulter les outils | Oui | Oui | Oui |
| Créer une mission et ses habilitations | Oui | Non | Non |
| Consulter / exporter une mission | Toutes | Missions affectées | Missions affectées |
| Documenter un test / suivre une correction | Oui | Missions affectées | Non |
| Clôturer / réouvrir une mission | Oui | Non | Non |
| Créer un utilisateur | Oui | Non | Non |
| Lire / exporter le journal global | Oui | Non | Non |
| Lire ses événements personnels | Oui | Non | Oui |

Un utilisateur sans rôle n’a pas accès aux fonctions métier. Le superutilisateur constitue le compte d’administration initial. L’application concerne un seul organisme ; elle ne fournit pas d’isolation multi-tenant.

## Préparer une mission

1. Obtenir l’autorisation écrite du propriétaire du système et en conserver l’original dans le référentiel documentaire de l’organisation.
2. L’administrateur crée une mission : référence d’autorisation, dates, IP ou réseaux CIDR, membres nominatifs. Les noms DNS ne sont pas acceptés dans cette version.
3. Vérifier le périmètre affiché. Les périodes sont évaluées en heure de Lagos ; les horodatages stockés sont gérés avec fuseau horaire.
4. Exécuter l’outil approuvé hors plateforme, dans l’environnement de test de l’organisation. Documenter sa version exacte et les paramètres. Cette plateforme n’exécute aucune commande réseau.

## Documenter et traiter les résultats

Depuis la mission, sélectionner **Documenter un test**. Fournir une IP appartenant au périmètre, une date de test passée comprise dans l’autorisation, la méthode, le constat, une preuve textuelle, la sévérité, une correction, un responsable et une échéance.

Supprimer les mots de passe, cookies, jetons et données personnelles inutiles des preuves avant saisie. Les champs de texte longs sont limités à 20 000 caractères. L’empreinte SHA-256 porte sur le texte enregistré en UTF-8, pas sur un fichier original. Conserver les originaux séparément si requis.

Les résultats initiaux ne sont pas modifiables depuis l’interface. En cas d’erreur, documenter un nouveau résultat explicitant la rectification. Le suivi permet « Ouvert », « En correction » et « Résolu ». Une résolution exige un commentaire de re-test ; l’application ne vérifie pas la véracité de ce commentaire. Une mission clôturée bloque la saisie et le suivi. Une mission hors période bloque les nouveaux résultats ; le suivi de corrections reste possible tant qu’elle est active.

## Constituer le dossier d’audit

1. Vérifier l’autorisation et la cohérence de la période avec les tests.
2. Examiner les preuves, la sévérité et les actions correctives. La sévérité est déclarative et ne calcule pas de score CVSS.
3. Exporter le rapport JSON depuis la mission ; l’export contient les preuves et leur empreinte.
4. Demander à l’administrateur l’extrait pertinent du journal global. L’auditeur ne voit dans l’interface que ses propres événements, afin de ne pas divulguer les autres missions.
5. Archiver le rapport avec les résultats originaux, la décision de recette et les signatures des responsables dans un stockage à rétention contrôlée.
6. Consigner les écarts aux contrôles ISO dans la matrice du rapport technique. Ne pas transformer un test réussi en déclaration de conformité générale.

## Administration des comptes

Créer les comptes dans **Utilisateurs** et transmettre le mot de passe initial par un canal sécurisé. Le rôle et l’activation peuvent ensuite être gérés depuis cette page avec un motif obligatoire. La modification du mot de passe se fait par l’administrateur système avec `python manage.py changepassword IDENTIFIANT` ; aucun parcours autonome de récupération ni MFA n’est livré.

La révocation et les changements de rôle se font par commande locale, avec motif obligatoire et journalisation :

```powershell
python manage.py set_access alice --disable --reason "Fin de mission"
python manage.py set_access alice --enable --role Auditeur --reason "Nouvelle habilitation"
```

Les comptes désactivés ne sont plus authentifiés par Django à la requête suivante. Les rôles sont relus à chaque requête. Les opérations directes de maintenance de base et `changepassword` ne sont pas inscrites dans le journal métier : conserver également un journal d’administration système.

## Incidents usuels

- **Accès refusé** : faire vérifier le rôle ; une mission non affectée renvoie 404.
- **Mission inactive** : vérifier les dates ou demander sa réouverture justifiée.
- **Trop de tentatives** : attendre l’expiration de la fenêtre de 15 minutes. Les tentatives sont limitées par compte et par IP.
- **Erreur CSRF** : recharger le formulaire, puis réessayer avec les cookies autorisés.
- **Preuve manquante** : un constat ne peut pas être marqué résolu sans commentaire de validation.
