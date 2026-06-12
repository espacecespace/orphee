# ORPHEE - Instructions projet

## Structure

- Le depot deploye sur Streamlit Cloud reste plat : `app.py`, les modules Python et les gabarits `.txt` doivent rester a la racine.
- La racine suivie par Git est la version de reference publiee.
- `web/` et `local/` sont des paquets de preparation non suivis. Quand une nouvelle version y est deposee, comparer avant de copier; ne jamais ecraser silencieusement la racine.
- Conserver tous les fichiers texte en UTF-8.

## Verification obligatoire

Avant chaque commit qui touche Python ou les gabarits :

1. `python scripts/validate_project.py`
2. `python -m pytest`
3. `python -m ruff check .`

Si `python` n'est pas disponible, utiliser un interpreteur Python 3.11+ valide et signaler clairement lequel a servi.

## Regles de changement

- Ne pas publier si la compilation ou les tests echouent.
- Ne pas telecharger de corpus NLTK pendant les tests unitaires; isoler le moteur phonetique avec des doublures lorsque necessaire.
- Ajouter un test pour toute correction de logique dans `orphee_core.py`.
- Garder l'interface Streamlit mince; placer la logique testable dans `orphee_core.py`.
- Ne jamais inclure de secret, jeton GitHub ou fichier `.env` dans Git.
- Le depot distant attendu est `https://github.com/espacecespace/orphee.git` sur la branche `main`.
