# ORPHÉE v8.1 — Streamlit Cloud

Version GitHub / Streamlit Cloud de l’interface guidée ORPHÉE.

## Déploiement

1. Créer un repo GitHub public ou privé.
2. Téléverser tout le contenu de ce dossier à la racine du repo.
3. Aller sur Streamlit Community Cloud.
4. Créer une nouvelle app.
5. Choisir le repo et définir `app.py` comme fichier principal.
6. Déployer.

## Fichiers requis à la racine

```text
app.py
orphee_core.py
moteur_phonetique.py
requirements.txt
README.md
.streamlit/config.toml
gabarits/
```

## Workflow utilisateur

L’interface guide l’utilisateur pas à pas :

1. Générer Prompt 1.
2. Copier Prompt 1 dans l’agent IA.
3. Coller Handoff 1 pour générer Prompt 2.
4. Coller Handoff 2 pour générer Prompt 3.
5. Coller le bloc final pur dans l’auditeur.

Les boutons de copie affichent les consignes de l’étape suivante directement dans l’interface.

## Confidentialité

Ne collez pas de paroles confidentielles dans une app publique. Oui, c’est le genre de conseil évident que les humains ignorent juste avant de créer un incident de confidentialité.
