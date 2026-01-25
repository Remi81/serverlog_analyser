# Instructions pour LLM / Intégration VSCode 🔧

## Contexte
- Fichier exemple fourni : `examples/logsat.log`
- Objectif : 2ᵉ version d'un analyseur de logs serveur qui permet à un utilisateur d'uploader un fichier de logs, d'analyser le contenu et d'obtenir des statistiques présentées sous forme de tableaux ou de graphiques.

---

## Objectifs fonctionnels 🎯
- Upload d'un fichier de log via l'interface graphique.
- Analyse du fichier et extraction de statistiques clés (liste ci‑dessous).
- Présentation claire dans une **table copiable** + **graphique(s)**.
- Option d'export / copie (CSV, TSV, JSON, Copy to clipboard) pour permettre le copier/coller.
- Interface au style sobre, lisible et accessible.

---

## Statistiques attendues (minimum) 📊
- Total de requêtes.
- Répartition par code HTTP (200, 3xx, 4xx, 5xx) — % et compte.
- Top endpoints (par nombre de requêtes).
- Top IPs (par nombre d'accès).
- Temps de réponse : min / mediane / moyenne / p95 / p99.
- Erreurs par période (ex.: par minute / par heure) — séries temporelles.
- Taille moyenne de réponse, si disponible.

> Extensions possibles : détection d’anomalies, regroupement par utilisateur, parsing d’autres formats (NGINX, Apache, syslog).

---

## Spécifications UI / UX ✨
- Page unique (SPA) : upload en haut, aperçu + contrôle de la source, puis résultats.
- Section "Tableau" : colonne triables, recherche, pagination et possibilité de sélectionner/copier des lignes. Boutons : `Copier le tableau`, `Télécharger CSV`.
- Section "Graphiques" : choix de graphiques (time series, histogramme, camembert pour statuts). Afficher légendes et tooltips.
- Thème : sobre — couleurs neutres, bon contraste, typographie lisible, espacement aéré.
- Accessibilité : support clavier, labels ARIA pour les contrôles.

---

## API / Backend 🔧
- Endpoint POST `/upload` pour upload du fichier (supporter streaming / multipart). Retour immédiat d'un job id ou analyse synchrone si fichiers petits.
- Endpoint GET `/jobs/<id>` pour récupérer état + résultats (progress, graphiques en JSON, tableau en CSV/JSON).
- Format de sortie standardisé (ex : JSON with arrays for timeseries and tabular rows).
- Tolérance aux lignes malformées : compter et exposer le nombre de lignes ignorées / erreurs de parsing.

---

## Format des données / Export 📁
- Fournir export CSV/TSV/JSON.
- Pour copier : implémenter une action qui met le CSV/TSV dans le presse‑papier (Clipboard API) et une autre qui copie le JSON sélectionné.
- Structures recommandées :
  - Table rows: [{timestamp, ip, method, path, status, size, duration, raw_line}]
  - Timeseries: [{timestamp_bucket, requests, errors, avg_duration}]

---

## Non‑fonctionnel / Qualité ✅
- Performance : capable d’analyser des fichiers de plusieurs dizaines de Mo sans OOM (use streaming, chunk parsing).
- Tests : unitaires pour le parsing et les calculs statistiques ; tests d’intégration pour l’upload et l’API ; tests UI minimal (Playwright / Cypress) pour flux upload → résultats.
- Sécurité : désactiver execution de fichiers uploadés, limiter taille, valider contenu.

---

## Stack & librairies conseillées (suggestion) 🧾
- Backend : **Python + FastAPI** (ou Flask). Parsing : `pandas` optionnel ou parsing streaming avec `regex`/`str.split`.
- Frontend : **React + TypeScript** (Vite), UI légère (Tailwind ou CSS modulaires). Charts : `Recharts`, `Chart.js` ou `Victory`.
- Tests : `pytest` pour Python, `Playwright` pour e2e.

---

## Critères d'acceptation (DoD) ✅
1. L'utilisateur peut uploader un fichier via l'UI et voir l'analyse commencer.
2. L'application affiche un tableau triable/recherchable/paginé contenant les données parsées.
3. L'utilisateur peut copier le tableau entier (Clipboard) ou télécharger un CSV.
4. Au moins deux graphiques (time series des requêtes, distribution des codes HTTP) sont visibles et interactifs.
5. Tests unitaires pour le parsing et statistiques avec couverture raisonnable.
6. Style sobre et accessible respecté.

---

## Tâches pour l'LLM / VSCode (Checklist pour PR) 🛠️
1. Créer le squelette projet (backend + frontend) si absent.
2. Implémenter le parsing streaming du fichier et les fonctions de calculs stats (avec tests unitaires).
3. Implémenter API d'upload et endpoint résultat (incl. gestion job si asynchrone).
4. Construire UI : upload, table, graphiques, export CSV & copy to clipboard.
5. Ajouter tests e2e couvrant le flux principal.
6. Documenter l'API et l'usage (README + exemples de commandes pour dev).
7. Ajouter tâches VSCode : `Run dev`, `Run tests`, `Lint`, `Format` dans `.vscode/tasks.json`.

---

## Template de prompt pour LLM (mode opératoire) 🤖
- Rôle : "Tu es un assistant dev qui implémente la fonctionnalité X. Respecte le style et les tests. Travaille en petites PRs."
- Exemples de consignes :
  - "Ajoute un endpoint `/upload` et un parser pour le format donné dans `examples/logsat.log`. Rédige tests unitaires pour 4 cas (ligne correcte, ligne malformée, fichier vide, grande ligne)."
  - "Crée un composant `LogResults` qui affiche un tableau copiable et deux graphiques; écris tests e2e qui uploadent `examples/logsat.log` et vérifient que la page montre >0 requêtes et permet le téléchargement CSV."
- Contraintes : commits atomiques, inclure tests, nommer les fichiers clairement, ajouter une courte description dans PR.

---

## Exemple de flux utilisateur (résumé) 🔁
1. Utilisateur ouvre l'app.
2. Clique sur `Choisir un fichier` → sélectionne `logsat.log` → clique sur `Analyser`.
3. Progress bar puis affichage du tableau + graphiques.
4. Utilisateur clique `Copier le tableau` ou `Télécharger CSV` et colle dans Excel / éditeur.

---

## Notes & bonnes pratiques 💡
- Rendre les sorties testables : fonctions pures pour parsing et stats (faciles à unit tester).
- Préférer des formats d'échange simples (CSV/JSON) pour l'export.
- Garder l'UI épurée : éviter animations lourdes pour rester sobre.

---

Si tu veux, je peux :
- Initialiser le squelette de projet et les fichiers de base.
- Écrire les tests unitaires du parser en premier pour guider le développement.

> Dis‑moi quelle action tu veux que je fasse maintenant (initialiser le projet / écrire le parser / créer le composant UI). ✨
