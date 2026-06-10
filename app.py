# ==============================================================================
# ORPHÉE-ULTRA v7 — Interface Web (Streamlit)
# Déploiement : Streamlit Community Cloud (streamlit.io/cloud)
#
# Nouveautés v7 :
#   • Aucune mention de Claude dans l'interface
#   • Titre automatique depuis le nom du fichier téléversé
#     (le titre saisi manuellement prévaut toujours)
#   • Gestionnaire d'hyperliens (ajouter / supprimer) depuis la page principale
#   • Bouton 📋 copier-coller sur chaque boîte de prompt généré
#   • Workflow bi-prompt :
#       Étape 1 → Prompt 1 généré + copié dans la plateforme IA
#       Étape 2 → Coller le résultat obtenu → générer le Prompt 2
# ==============================================================================

import os
import streamlit as st

# ── Configuration de la page ──────────────────────────────────────────────────
st.set_page_config(
    page_title="ORPHÉE-ULTRA — Générateur de Prompt",
    page_icon="🎵",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS personnalisé ──────────────────────────────────────────────────────────
st.markdown("""
<style>
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
    div[data-testid="stTextArea"] textarea {
        font-family: 'Courier New', 'Consolas', monospace;
        font-size: 0.84rem;
        line-height: 1.55;
    }
    div[data-testid="stDownloadButton"] > button {
        width: 100%;
    }
    .section-label {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        opacity: 0.5;
        margin-bottom: 0.2rem;
    }
    .link-pill {
        display: inline-block;
        background: #1e1e2e;
        color: #cdd6f4;
        border-radius: 999px;
        padding: 0.2rem 0.75rem;
        font-size: 0.82rem;
        margin: 0.15rem 0.2rem;
        text-decoration: none;
    }
    .link-pill:hover { opacity: 0.8; }
    .prompt-header {
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #888;
        margin-bottom: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Initialisation de la session ──────────────────────────────────────────────
if "liens" not in st.session_state:
    st.session_state.liens = [
        {"label": "ChatGPT", "url": "https://chat.openai.com"},
        {"label": "Gemini",  "url": "https://gemini.google.com"},
    ]

if "prompt1_result" not in st.session_state:
    st.session_state.prompt1_result = ""

if "titre_final" not in st.session_state:
    st.session_state.titre_final = ""

if "yaourt_cache" not in st.session_state:
    st.session_state.yaourt_cache = ""

if "langue_detectee" not in st.session_state:
    st.session_state.langue_detectee = ""


# ── Chargement du moteur phonétique (une fois au démarrage) ──────────────────
@st.cache_resource(show_spinner=False)
def setup_moteur():
    import nltk
    for corpus in ["averaged_perceptron_tagger",
                   "averaged_perceptron_tagger_eng",
                   "cmudict"]:
        nltk.download(corpus, quiet=True)
    from moteur_phonetique import analyser_ADN_phonetique  # noqa: F401
    return True


# ── Chargement des gabarits ───────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def charger_gabarits():
    base = os.path.dirname(os.path.abspath(__file__))
    def lire(nom):
        chemin = os.path.join(base, nom)
        with open(chemin, "r", encoding="utf-8") as fh:
            return fh.read()
    return lire("GABARIT_ORPHEE_CREATIF_v7.txt"), lire("GABARIT_ORPHEE_EDITORIAL_v7_TEMPLATE.txt")


# ── Démarrage ─────────────────────────────────────────────────────────────────
with st.spinner("Chargement du moteur phonétique… (30–60 s au premier démarrage)"):
    setup_moteur()

gabarit_1, gabarit_2 = charger_gabarits()


# ── En-tête ───────────────────────────────────────────────────────────────────
st.markdown('<p class="orphee-title">🎵 ORPHÉE-ULTRA</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="orphee-sub">Générateur de prompt · v7 · g2p_en + CMUDict</p>',
    unsafe_allow_html=True,
)

# ── Liens vers les plateformes IA ─────────────────────────────────────────────
st.markdown("**Plateformes IA**")

if st.session_state.liens:
    pills_html = "".join(
        f'<a class="link-pill" href="{l["url"]}" target="_blank">🔗 {l["label"]}</a>'
        for l in st.session_state.liens
    )
    st.markdown(pills_html, unsafe_allow_html=True)
else:
    st.caption("Aucun lien enregistré.")

with st.expander("✏️ Gérer les liens"):
    st.markdown("**Ajouter un lien**")
    col_a, col_b, col_c = st.columns([2, 3, 1])
    with col_a:
        new_label = st.text_input("Nom", placeholder="Ex : Mistral", key="new_label", label_visibility="collapsed")
    with col_b:
        new_url = st.text_input("URL", placeholder="https://…", key="new_url", label_visibility="collapsed")
    with col_c:
        if st.button("Ajouter", key="btn_add_link"):
            if new_label.strip() and new_url.strip():
                st.session_state.liens.append({"label": new_label.strip(), "url": new_url.strip()})
                st.rerun()
            else:
                st.warning("Remplissez le nom et l'URL.")

    if st.session_state.liens:
        st.markdown("**Supprimer un lien**")
        options = [f"{l['label']} — {l['url']}" for l in st.session_state.liens]
        a_supprimer = st.selectbox("Choisir", options, key="del_link_sel", label_visibility="collapsed")
        if st.button("Supprimer", key="btn_del_link"):
            idx = options.index(a_supprimer)
            st.session_state.liens.pop(idx)
            st.rerun()

st.divider()


# ── Aide ──────────────────────────────────────────────────────────────────────
with st.expander("ℹ️ Comment utiliser"):
    st.markdown("""
**Étape 1 — Générer le Prompt 1 (Créatif)**
1. Saisissez un titre ou téléversez un fichier `.txt` (le titre sera extrait automatiquement).
2. Collez ou téléversez votre yaourt rythmique.
3. Cliquez **Générer le Prompt 1**.
4. Copiez le prompt (bouton 📋) et collez-le dans la plateforme IA de votre choix.

**Étape 2 — Générer le Prompt 2 (Éditorial)**
1. Revenez dans l'app et collez le résultat obtenu dans la zone **Handoff Package**.
2. Cliquez **Générer le Prompt 2**.
3. Copiez et utilisez ce second prompt pour la phase éditoriale.

**Balises de section acceptées :**  
`[VERSE]`, `[CHORUS]`, `[PRE-CHORUS]`, `[BRIDGE]`, `[OUTRO]`, etc.
""")

st.divider()


# ── SECTION 1 : Saisie du yaourt ─────────────────────────────────────────────
st.markdown("### 📝 Étape 1 — Yaourt & Prompt Créatif")

titre_saisi = st.text_input(
    "Titre de la chanson",
    placeholder="Ex : FOREVER LOST  (laissez vide pour utiliser le nom du fichier)",
    key="titre_input",
)

st.markdown('<p class="section-label">Yaourt</p>', unsafe_allow_html=True)
mode = st.radio(
    "Mode de saisie",
    ["✏️  Coller le texte", "📁  Téléverser un fichier .txt"],
    horizontal=True,
    key="mode_saisie",
    label_visibility="collapsed",
)

yaourt = ""
titre_depuis_fichier = ""

if mode == "✏️  Coller le texte":
    yaourt = st.text_area(
        "Yaourt",
        height=280,
        placeholder=(
            "[VERSE]\nda DUM da da DUM da DUM\nDUM da da DUM da DUM da\n\n"
            "[CHORUS]\nda DUM DUM da da da DUM\nDUM da DUM da da DUM da"
        ),
        key="yaourt_text",
        label_visibility="collapsed",
    )
else:
    fichier = st.file_uploader("Fichier .txt", type=["txt"],
                               label_visibility="collapsed", key="fichier_up")
    if fichier:
        yaourt = fichier.read().decode("utf-8")
        # Extraire le titre depuis le nom de fichier (sans extension)
        nom_brut = os.path.splitext(fichier.name)[0]
        titre_depuis_fichier = nom_brut.replace("_", " ").replace("-", " ").upper()
        st.text_area("Aperçu", value=yaourt, height=200,
                     disabled=True, label_visibility="visible")
    else:
        st.caption("Aucun fichier sélectionné.")

# Titre effectif : manuel > fichier > défaut
titre_final = (
    titre_saisi.strip().upper() if titre_saisi.strip()
    else titre_depuis_fichier if titre_depuis_fichier
    else "CHANSON SANS TITRE"
)

if titre_depuis_fichier and not titre_saisi.strip():
    st.info(f"🎵 Titre extrait du fichier : **{titre_final}**")

# ── Bouton Prompt 1 ───────────────────────────────────────────────────────────
if st.button("🎵 Générer le Prompt 1", type="primary",
             use_container_width=True, key="btn_p1"):
    if not yaourt.strip():
        st.error("❌ Aucun yaourt saisi.")
        st.stop()

    with st.spinner("Analyse phonétique et assemblage du Prompt 1…"):
        try:
            from generateur_orphee_v7 import assembler_prompt_1
            p1, langue, nb = assembler_prompt_1(gabarit_1, titre_final, yaourt)
            st.session_state.prompt1_result = p1
            st.session_state.titre_final = titre_final
            st.session_state.yaourt_cache = yaourt
            st.session_state.langue_detectee = langue
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
            st.exception(e)
            st.stop()


# ── Affichage du Prompt 1 ─────────────────────────────────────────────────────
if st.session_state.prompt1_result:
    p1 = st.session_state.prompt1_result
    langue = st.session_state.langue_detectee
    titre_af = st.session_state.titre_final

    st.success(f"✅ Prompt 1 généré — Langue détectée : **{langue}**")

    st.markdown('<p class="prompt-header">Prompt 1 — Créatif</p>', unsafe_allow_html=True)

    # Bouton copier via composant HTML/JS
    st.components.v1.html(f"""
        <button onclick="
            navigator.clipboard.writeText(document.getElementById('p1txt').innerText)
                .then(() => this.innerText = '✅ Copié !')
                .catch(() => this.innerText = '❌ Échec');
            setTimeout(() => this.innerText = '📋 Copier le Prompt 1', 2000);
        " style="
            background:#2563eb; color:#fff; border:none; border-radius:8px;
            padding:0.45rem 1.1rem; font-size:0.88rem; cursor:pointer;
            margin-bottom:0.5rem; font-weight:600;
        ">📋 Copier le Prompt 1</button>
        <pre id="p1txt" style="display:none">{p1.replace('<','&lt;').replace('>','&gt;')}</pre>
    """, height=60)

    st.text_area("Prompt 1", value=p1, height=360,
                 key="out_p1", label_visibility="collapsed")

    nom_dl_1 = f"{titre_af.replace(' ', '_')}_PROMPT1_CREATIF.txt"
    st.download_button("⬇️ Télécharger le Prompt 1 (.txt)",
                       data=p1, file_name=nom_dl_1,
                       mime="text/plain", use_container_width=True, key="dl_p1")

    st.caption(f"{len(p1):,} caractères · {p1.count(chr(10)):,} lignes · `{nom_dl_1}`")

    st.divider()

    # ── SECTION 2 : Handoff + Prompt 2 ───────────────────────────────────────
    st.markdown("### 📬 Étape 2 — Handoff Package & Prompt Éditorial")
    st.markdown(
        "Collez ici le **résultat complet** renvoyé par la plateforme IA "
        "après avoir utilisé le Prompt 1 ci-dessus."
    )

    handoff = st.text_area(
        "Handoff Package",
        height=280,
        placeholder="Collez ici le résultat obtenu de la plateforme IA (paroles, tableau, notes…)",
        key="handoff_input",
        label_visibility="collapsed",
    )

    if st.button("🎼 Générer le Prompt 2", type="primary",
                 use_container_width=True, key="btn_p2"):
        if not handoff.strip():
            st.error("❌ Collez d'abord le Handoff Package avant de générer le Prompt 2.")
            st.stop()

        with st.spinner("Assemblage du Prompt 2 (Éditorial)…"):
            try:
                from generateur_orphee_v7 import assembler_prompt_2
                p2, langue2 = assembler_prompt_2(
                    gabarit_2,
                    st.session_state.titre_final,
                    st.session_state.yaourt_cache,
                    handoff,
                )
            except Exception as e:
                st.error(f"❌ Erreur : {e}")
                st.exception(e)
                st.stop()

        st.success(f"✅ Prompt 2 généré — Langue : **{langue2}**")

        st.markdown('<p class="prompt-header">Prompt 2 — Éditorial</p>', unsafe_allow_html=True)

        # Bouton copier Prompt 2
        st.components.v1.html(f"""
            <button onclick="
                navigator.clipboard.writeText(document.getElementById('p2txt').innerText)
                    .then(() => this.innerText = '✅ Copié !')
                    .catch(() => this.innerText = '❌ Échec');
                setTimeout(() => this.innerText = '📋 Copier le Prompt 2', 2000);
            " style="
                background:#7c3aed; color:#fff; border:none; border-radius:8px;
                padding:0.45rem 1.1rem; font-size:0.88rem; cursor:pointer;
                margin-bottom:0.5rem; font-weight:600;
            ">📋 Copier le Prompt 2</button>
            <pre id="p2txt" style="display:none">{p2.replace('<','&lt;').replace('>','&gt;')}</pre>
        """, height=60)

        st.text_area("Prompt 2", value=p2, height=360,
                     key="out_p2", label_visibility="collapsed")

        titre_af = st.session_state.titre_final
        nom_dl_2 = f"{titre_af.replace(' ', '_')}_PROMPT2_EDITORIAL.txt"
        st.download_button("⬇️ Télécharger le Prompt 2 (.txt)",
                           data=p2, file_name=nom_dl_2,
                           mime="text/plain", use_container_width=True, key="dl_p2")

        st.caption(f"{len(p2):,} caractères · {p2.count(chr(10)):,} lignes · `{nom_dl_2}`")
