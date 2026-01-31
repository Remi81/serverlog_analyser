# Setup rapide du projet (venv) 🇫🇷

But: permettre un environnement isolé pour installer les dépendances sans polluer le système global.

Prérequis
- Avoir Python 3.9+ installé (ou 3.10/3.11 recommandé).

Commandes (Linux)
1. Créer le venv dans le dossier du projet :
   python3 -m venv .venv  # utiliser `python3` si `python` pointe vers Python 2 ; sinon `python -m venv .venv` fonctionne

2. Activer le venv :
   source .venv/bin/activate

   # Vérifier la version : `python3 --version` ou `python --version`

3. Mettre pip à jour et installer les dépendances :
   pip install -U pip
   pip install -r requirements.txt

4. Lancer le serveur de dev :
   # Avec reload (recommandé pour le dev) :
   uvicorn main:app --reload --host 127.0.0.1 --port 8000

   # Si tu as des problèmes de "Too many open files" avec le watcher, lance sans reload :
   uvicorn main:app --host 127.0.0.1 --port 8000

5. Lancer les tests :
   - Depuis le venv activé :
     ```bash
     source .venv/bin/activate
     pytest
     ```
   - Sans activer le venv (commande directe) :
     ```bash
     .venv/bin/pytest -q
     ```
   - Exécuter un test précis :
     ```bash
     .venv/bin/pytest tests/test_parser.py::test_aggregated_paths_counts -q
     ```
   - Astuce VSCode : ajoute une tâche (`.vscode/tasks.json`) pour lancer les tests rapidement, ou utilise la fonctionnalité "Python: Run Tests" configurée sur pytest.

## Troubleshooting — Too many open files ⚠️
Si tu vois une erreur « Too many open files (os error 24) » avec `--reload`, c'est lié à la limite de descripteurs ouverts du système. Vérifier la limite actuelle :

```
ulimit -n
```

Tu peux l'augmenter temporairement pour ta session :

```
ulimit -n 65536
```

Ou l'augmenter de façon permanente pour ton utilisateur (ex. ajouter dans `/etc/security/limits.conf`) :

```
<user> soft nofile 65536
<user> hard nofile 65536
```

Après modification, reconnecte-toi pour que les changements prennent effet.

Notes courtes
- Pour désactiver le venv : `deactivate`.
- Dans VSCode : ouvrez la palette (Ctrl+Shift+P) → "Python: Select Interpreter" → choisissez le `.venv` du projet.
- Gardez le venv dans `.gitignore` pour ne pas commiter les dépendances.