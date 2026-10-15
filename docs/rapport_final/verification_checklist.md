# Checklist de conformité — Rapport final AuditHub

Date de contrôle : 15 octobre 2026.

## Référence obligatoire

- [x] `Structure rapport.docx` lu intégralement : corps, tableaux, en-têtes et pieds de page.
- [x] Couleurs inspectées au niveau des runs Word ; rouge identifié par `EE0000`.
- [x] Texte rouge exclu du rapport final.
- [x] Titres noirs conservés dans l'ordre : Informations générales, Objectifs, Périmètre, Critères, Équipe, Méthodologie, Déroulement, Synthèse, Non-conformités, Observations, Conclusion, Annexes.
- [x] Sous-titres noirs 1.3, 1.4, 3.2, 4.1–4.3, 6.1–6.2, 7.1–7.2, 8.1–8.2, 11.1 et 11.4 conservés.
- [x] Sections rouges du modèle non reproduites comme contenu imposé.

## Correspondance des sections

| Section | Contenu AuditHub vérifié | Sources principales |
|---|---|---|
| 1. Informations générales | contexte, problème, technologies, nature de la revue | README, dépendances |
| 2. Objectifs | objectifs fonctionnels, sécurité, critères de réussite | README, tests |
| 3. Périmètre | composants, processus, exclusions, dépendances | arborescence, architecture |
| 4. Critères | mesures ciblées, documentation officielle, limites des exigences client | docs, références officielles |
| 5. Équipe | identités non communiquées, acteurs applicatifs et cas d’utilisation | groupes Django, permissions |
| 6. Méthodologie | revue, architecture, flux, modèle de données, séquence | code, migrations |
| 7. Déroulement | chronologie, backend, frontend, sécurité, démonstration | vues, formulaires, React |
| 8. Synthèse | résultats vérifiés, contribution A.8.8/A.8.25/A.8.29 | tests, rapport ISO |
| 9. Non-conformités | limites techniques sans fausse qualification ISO | code et architecture |
| 10. Observations | accessibilité, CVSS, CI, intégration future | frontend, docs |
| 11. Conclusion | validation du logiciel et absence de recommandation ISO | ensemble des preuves |
| 12. Annexes | documents, code, RBAC, endpoints et preuves | dépôt complet |

## Exactitude technique

- [x] 33 tests Django réellement exécutés et réussis.
- [x] 3 parcours Playwright réellement exécutés et réussis.
- [x] Build React réellement compilé.
- [x] Migrations synchronisées et checks Django sans erreur.
- [x] Modèles, relations, contraintes et endpoints recoupés avec les sources.
- [x] RBAC recoupé avec `portal/security.py` et les décorateurs de vues.
- [x] Limites explicitement distinguées des fonctionnalités livrées.
- [x] Aucune certification, garantie de sécurité ou fonction d’outil offensif inventée.
- [x] Identité de l’auteur, professeur et organisme laissée « non communiquée ».

## Figures et captures

- [x] 9 captures authentiques réalisées avec Playwright et Chrome headless.
- [x] Base SQLite temporaire distincte ; aucune donnée de production modifiée.
- [x] Données de démonstration synthétiques et non sensibles.
- [x] Aucune capture d’une page vide, en chargement ou en erreur après reprise automatisée.
- [x] Diagrammes TikZ dérivés du code : architecture, cas d’utilisation, workflow, entités et séquence.
- [x] Figures assorties de légendes, labels et références.

Captures intégrées : connexion, création de mission, saisie d’un résultat, détail de mission, historique du suivi, tableau de bord, utilisateurs/rôles, journal et matrice ISO.

## Compilation et inspection

- [x] PDF compilé avec MiKTeX/pdfLaTeX et BibTeX.
- [x] 39 pages, 12 chapitres, aucune page vide.
- [x] Table des matières, liste des figures, liste des tableaux et pagination présentes.
- [x] Références et citations résolues.
- [x] Aucun débordement `Overfull` après la compilation finale.
- [x] Pages représentatives rendues avec PyMuPDF et inspectées visuellement.
- [x] Aucun marqueur rouge `EE0000` ni placeholder `[Nom]`, `[Date]` ou `[X]` dans le texte extrait.

## Limitations à compléter par le porteur

- Nom de l’étudiant, établissement, formation, professeur/encadrant et année académique non communiqués.
- Sujet initial détaillé, grille de notation et informations institutionnelles non présents dans le dépôt.
- Aucun environnement de production, mandat de certification ou preuve organisationnelle fourni.
