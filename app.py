# ==============================================================================
# ORPHÉE-ULTRA — Interface Web (Streamlit)
# Déploiement : Streamlit Community Cloud (streamlit.io/cloud)
# ==============================================================================

import os
import streamlit as st

# ── Configuration de la page (doit être le 1er appel Streamlit) ───────────────
st.set_page_config(
    page_title="ORPHÉE-ULTRA — Générateur de Prompt",
    page_icon="🎵",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS personnalisé ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Titre principal */
    .orphee-title {
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        margin-bottom: 0;
    }
    .orphee-sub {
        font-size: 0.85rem;
        opacity: 0.55;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-top: 0.1rem;
        margin-bottom: 1.5rem;
    }
    /* Zone de saisie en monospace pour le yaourt */
    div[data-testid="stTextArea"] textarea {
        font-family: 'Courier New', 'Consolas', monospace;
        font-size: 0.84rem;
        line-height: 1.55;
    }
    /* Bouton de téléchargement pleine largeur */
    div[data-testid="stDownloadButton"] > button {
        width: 100%;
    }
    /* Étiquettes de section */
    .section-label {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        opacity: 0.5;
        margin-bottom: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Chargement et mise en cache du moteur phonétique ─────────────────────────
# Se déclenche une seule fois par démarrage du serveur (cold start).
# Les données NLTK sont téléchargées si elles sont absentes.
@st.cache_resource(show_spinner=False)
def setup_moteur():
    import nltk
    for corpus in [
        "averaged_perceptron_tagger",
        "averaged_perceptron_tagger_eng",
        "cmudict",
    ]:
        nltk.download(corpus, quiet=True)
    # Pré-charger le modèle g2p pour que la 1ère génération soit rapide
    from moteur_phonetique import analyser_ADN_phonetique  # noqa: F401
    return True


# ── Chargement et mise en cache du gabarit ────────────────────────────────────
@st.cache_data(show_spinner=False)
def charger_gabarit():
    base = os.path.dirname(os.path.abspath(__file__))
    chemin = os.path.join(base, "GABARIT_ORPHEE_ULTRA_v5_EN.txt")
    with open(chemin, "r", encoding="utf-8") as fh:
        return fh.read()


# ── Fonction de génération ────────────────────────────────────────────────────
def generer_prompt(titre: str, yaourt: str, gabarit: str):
    from generateur_orphee_v5 import (
        detecter_langue,
        analyser_paroles_vers_tableau,
        injecter_tableau,
    )
    lignes = yaourt.splitlines(keepends=True)
    langue = detecter_langue(yaourt)
    tableau = analyser_paroles_vers_tableau(lignes)

    prompt = gabarit
    prompt = prompt.replace("[TITRE_DE_LA_CHANSON_AUTOMATIQUE]", titre.upper().strip())
    prompt = prompt.replace("[LANGUE_DÉTÉCTÉE]", langue)
    prompt = injecter_tableau(prompt, tableau)
    return prompt, langue


# ── Démarrage ─────────────────────────────────────────────────────────────────
with st.spinner("Chargement du moteur phonétique… (30–60 s au premier démarrage)"):
    setup_moteur()

gabarit = charger_gabarit()


# ── En-tête ───────────────────────────────────────────────────────────────────
st.markdown('<p class="orphee-title">🎵 ORPHÉE-ULTRA</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="orphee-sub">Générateur de prompt · v5 · g2p_en + CMUDict</p>',
    unsafe_allow_html=True,
)

with st.expander("ℹ️ Comment utiliser"):
    st.markdown("""
**1. Titre** — Donnez un nom à la chanson (optionnel, mais recommandé).

**2. Yaourt** — Collez votre texte de placeholder rythmique ou téléversez un `.txt`.  
Structurez avec des balises de section entre crochets :
```
[VERSE]
da DUM da da DUM da DUM
DUM da da DUM da DUM da

[CHORUS]
DUM da da DUM DUM da da DUM
```
Balises acceptées : `[VERSE]`, `[CHORUS]`, `[PRE-CHORUS]`, `[BRIDGE]`, `[OUTRO]`, etc.

**3. Générer** — Cliquez sur le bouton. Le prompt assemblé peut ensuite être copié ou téléchargé, puis collé dans Claude.

**Modifier le gabarit** — Éditez directement `GABARIT_ORPHEE_ULTRA_v5_EN.txt` dans GitHub. L'app se redéploie automatiquement.
""")

st.divider()


# ── Formulaire de saisie ──────────────────────────────────────────────────────
titre = st.text_input(
    "Titre de la chanson",
    placeholder="Ex : FOREVER LOST",
    help="Injecté aux emplacements [TITRE_DE_LA_CHANSON_AUTOMATIQUE] dans le gabarit.",
)

st.markdown('<p class="section-label">Yaourt</p>', unsafe_allow_html=True)
mode = st.radio(
    "Mode de saisie",
    ["✏️  Coller le texte", "📁  Téléverser un fichier .txt"],
    horizontal=True,
    label_visibility="collapsed",
)

if mode == "✏️  Coller le texte":
    yaourt = st.text_area(
        "Yaourt",
        height=320,
        placeholder=(
            "[VERSE]\n"
            "da DUM da da DUM da DUM\n"
            "DUM da da DUM da DUM da\n\n"
            "[CHORUS]\n"
            "da DUM DUM da da da DUM\n"
            "DUM da DUM da da DUM da"
        ),
        help="Les lignes commençant par [BALISE] définissent les sections.",
        label_visibility="collapsed",
    )
else:
    fichier = st.file_uploader(
        "Fichier .txt",
        type=["txt"],
        label_visibility="collapsed",
    )
    if fichier:
        yaourt = fichier.read().decode("utf-8")
        st.text_area(
            "Aperçu du fichier",
            value=yaourt,
            height=220,
            disabled=True,
            label_visibility="visible",
        )
    else:
        yaourt = ""
        st.caption("Aucun fichier sélectionné.")

st.divider()

# ── Bouton principal ──────────────────────────────────────────────────────────
generer = st.button(
    "🎵 Générer le prompt",
    type="primary",
    use_container_width=True,
)


# ── Génération et affichage du résultat ───────────────────────────────────────
if generer:
    if not yaourt.strip():
        st.error("❌ Aucun yaourt saisi. Collez ou téléversez votre texte avant de générer.")
        st.stop()

    titre_final = titre.strip() if titre.strip() else "CHANSON SANS TITRE"
    if not titre.strip():
        st.info("ℹ️ Aucun titre saisi — « CHANSON SANS TITRE » utilisé par défaut.")

    with st.spinner("Analyse phonétique et assemblage du prompt…"):
        try:
            prompt_result, langue = generer_prompt(titre_final, yaourt, gabarit)
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération : {e}")
            st.exception(e)
            st.stop()

    st.success(f"✅ Prompt généré — Langue détectée : **{langue}**")

    st.text_area(
        "Prompt — à coller dans Claude",
        value=prompt_result,
        height=420,
        key="output_prompt",
    )

    nom_fichier_dl = f"{titre_final.replace(' ', '_')}_PROMPT.txt"
    st.download_button(
        label="⬇️  Télécharger le prompt (.txt)",
        data=prompt_result,
        file_name=nom_fichier_dl,
        mime="text/plain",
        use_container_width=True,
    )

    nb_lignes = prompt_result.count('\n')
    st.caption(f"Prompt : {len(prompt_result):,} caractères · {nb_lignes:,} lignes · fichier : `{nom_fichier_dl}`")
