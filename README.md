# ORPHÉE v8.2 — Version Streamlit Cloud SANS SOUS-DOSSIERS

Cette version est faite pour éviter le cauchemar GitHub des sous-dossiers. Tous les fichiers doivent être téléversés **à la racine** du dépôt GitHub.

## Fichiers à mettre dans GitHub

Téléversez exactement ces fichiers, tous au même endroit, sans créer de dossier :

```text
app.py
orphee_core.py
moteur_phonetique.py
auditeur_final_cli.py
requirements.txt
README.md
ORPHEE_SOURCE_PROMPT_1_v1_2_FINAL.txt
ORPHEE_TOPLINER_PROMPT_2_v1_0_FINAL.txt
ORPHEE_FINALIZER_PROMPT_3_v1_0_FINAL.txt
ORPHEE_AUDIT_CORRECTION_v1_0.txt
```

## Déploiement sur Streamlit Cloud

1. Créez un nouveau dépôt GitHub.
2. Cliquez sur **Add file** → **Upload files**.
3. Glissez uniquement les fichiers listés ci-dessus dans la zone GitHub.
4. Cliquez sur **Commit changes**.
5. Dans Streamlit Cloud, créez une nouvelle app.
6. Choisissez le repo.
7. Main file path : `app.py`
8. Cliquez sur **Deploy**.

## Notes

- Aucun sous-dossier n'est nécessaire.
- Aucun fichier `.streamlit/config.toml` n'est nécessaire.
- Aucun fichier `.bat` n'est nécessaire pour Streamlit Cloud.
- Si l'app échoue au premier démarrage, ouvrez les logs Streamlit Cloud et vérifiez que tous les fichiers ci-dessus sont bien à la racine.

## Usage de l'app

1. Coller ou téléverser le yaourt → générer Prompt 1.
2. Copier Prompt 1 dans l'IA → récupérer Handoff 1.
3. Coller Handoff 1 → générer Prompt 2.
4. Copier Prompt 2 dans l'IA → récupérer Handoff 2.
5. Coller Handoff 2 → générer Prompt 3.
6. Coller le bloc final pur → audit local + prompt de correction.


## v8.3 — Correction du bloc final Prompt 3

Le Prompt 3 demande maintenant que le bloc `FINAL HANDOFF — PURE LYRICS ONLY` soit rendu dans un bloc de code `text` pour faciliter la copie.
L'auditeur accepte maintenant :

- le bloc pur seul ;
- toute la sortie Prompt 3 complète ;
- un bloc avec ou sans lignes vides entre les sections ;
- un bloc entouré de ```text.

L'app extrait et normalise automatiquement le bloc final avant l'audit.


## Note v8.5 — Virgules et partitions

L'audit vérifie maintenant explicitement que les partitions internes du blueprint sont respectées. Une ligne avec le bon total syllabique peut être rejetée si elle ne respecte pas les pauses internes issues des virgules, points, tirets ou autres séparateurs du yaourt source. Exemple : `[2] + [14]` n'est pas équivalent à `[16]`. Oui, c'est strict. C'est le but, malheureusement pour les phrases trop propres.


## Note v8.5

Ajout du verrou **Strong Attack / Held Note Lock** : les attaques fortes et notes tenues ne doivent pas tomber sur des articles/prépositions faibles lorsque la source portait un mot fort.
