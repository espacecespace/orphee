# ORPHÉE v10.0 Candidate-Gated

Cette version ajoute un Candidate Gate local : Prompt 1 doit produire un pool de 8 fondations et un bloc `FOUNDATION GATE OUTPUT — SELECTED CANDIDATE`. L’app bloque Prompt 2 si ce bloc manque ou s’il retombe dans une famille dramaturgique interdite/refuge. Prompt 2 et Prompt 3 ont aussi des Quality Gates pré-final. Oui, le portique existe enfin avant la piste de décollage.

# ORPHÉE v9.0 — Version Streamlit Cloud SANS SOUS-DOSSIERS

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


## v9.0 — Correction du bloc final Prompt 3

Le Prompt 3 demande maintenant que le bloc `FINAL HANDOFF — PURE LYRICS ONLY` soit rendu dans un bloc de code `text` pour faciliter la copie.
L'auditeur accepte maintenant :

- le bloc pur seul ;
- toute la sortie Prompt 3 complète ;
- un bloc avec ou sans lignes vides entre les sections ;
- un bloc entouré de ```text.

L'app extrait et normalise automatiquement le bloc final avant l'audit.


## Note v9.0 — Virgules et partitions

L'audit vérifie maintenant explicitement que les partitions internes du blueprint sont respectées. Une ligne avec le bon total syllabique peut être rejetée si elle ne respecte pas les pauses internes issues des virgules, points, tirets ou autres séparateurs du yaourt source. Exemple : `[2] + [14]` n'est pas équivalent à `[16]`. Oui, c'est strict. C'est le but, malheureusement pour les phrases trop propres.


## Note v9.0

Ajout du verrou **Strong Attack / Held Note Lock** : les attaques fortes et notes tenues ne doivent pas tomber sur des articles/prépositions faibles lorsque la source portait un mot fort.

## Note v9.0

Les noms de fichiers des gabarits sont inchangés. Cette version ajoute seulement des règles internes : Anchor-First, réparation bornée, verrou anti-ponctuation parasite et prudence de validation locale.


## Notes v9.0

- Le script local calcule maintenant un **Creative Coordinate Divergence Package** à partir du titre, du blueprint, de la ligne 7, de la dernière ligne, du nombre de sections, des partitions et des lignes courtes.
- Prompt 1 utilise ces coordonnées pour générer des moteurs humains plus divergents sans dépendre d'une banlist de mots.
- Prompt 2 conserve les verrous v9.0 : partition, attaques fortes, no-extra-punctuation, anchor-first et repair borné.
- Prompt 3 ajoute un audit de fonction dramatique pour éviter le synonym laundering et les attracteurs récurrents.
- L'auditeur local ajoute un **Attractor Function Report** qualitatif, séparé des erreurs mécaniques.


## v9.0

Ajoute un Run Salt, un paquet de divergence créative injecté et visible dans Prompt 1, un veto de familiarité, et un diagnostic du paquet créatif dans l’interface.


## Diagnostic v9.0
L’interface affiche la version active, le chemin réel de `orphee_core.py` et le rapport d’audit commence par `AUDIT ENGINE VERSION: ORPHÉE v9.0 QUALITY GATE`. Si cette ligne est absente, le mauvais moteur tourne.
