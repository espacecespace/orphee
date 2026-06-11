# -*- coding: utf-8 -*-
"""
ORPHÉE v8 — Interface Streamlit guidée
=======================================
Workflow : Prompt 1 → Prompt 2 → Prompt 3 → Audit final.
Interface pensée pour un usage local ou Streamlit Cloud.
"""

from __future__ import annotations

import json
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

from orphee_core import (
    BuildContext,
    assembler_prompt_1,
    assembler_prompt_2,
    assembler_prompt_3,
    audit_final_text,
    build_context,
    build_correction_prompt,
    extract_final_pure_lyrics,
    normalize_title_from_filename,
    slugify_filename,
)

APP_VERSION = "v8.1 friendly"

st.set_page_config(
    page_title="ORPHÉE — Générateur guidé",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
:root {
  --orphee-bg-soft: rgba(91, 141, 239, .08);
  --orphee-border: rgba(120, 130, 160, .24);
  --orphee-text-muted: rgba(120, 120, 140, .95);
}
.block-container {max-width: 1180px; padding-top: 2rem; padding-bottom: 4rem;}
.orphee-hero {
  padding: 1.35rem 1.55rem;
  border-radius: 1.25rem;
  border: 1px solid var(--orphee-border);
  background: linear-gradient(135deg, rgba(80,120,255,.14), rgba(170,90,255,.10));
  margin-bottom: 1.15rem;
}
.orphee-title {font-size: 2.25rem; font-weight: 900; letter-spacing: -.02em; margin: 0;}
.orphee-sub {font-size: .98rem; color: var(--orphee-text-muted); margin-top: .25rem; margin-bottom: 0;}
.step-grid {display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap:.65rem; margin: 1rem 0 1.25rem;}
.step-pill {
  border: 1px solid var(--orphee-border);
  border-radius: .9rem;
  padding: .8rem .9rem;
  background: rgba(255,255,255,.035);
}
.step-pill.done {background: rgba(40, 180, 100, .12); border-color: rgba(40, 180, 100, .35);}
.step-pill.open {background: rgba(70, 120, 240, .13); border-color: rgba(70, 120, 240, .38);}
.step-pill.locked {opacity: .55;}
.step-num {font-size:.72rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; color:var(--orphee-text-muted);}
.step-title {font-weight:800; margin-top:.12rem;}
.step-desc {font-size:.82rem; color:var(--orphee-text-muted); margin-top:.12rem;}
.card {
  border: 1px solid var(--orphee-border);
  border-radius: 1.1rem;
  padding: 1.1rem 1.25rem;
  background: rgba(255,255,255,.03);
  margin-bottom: 1rem;
}
.card h3 {margin-top: 0;}
.card-soft {background: var(--orphee-bg-soft);}
.success-callout {
  border-left: 5px solid #22a06b;
  background: rgba(34,160,107,.12);
  padding: .85rem 1rem;
  border-radius: .75rem;
  margin: .75rem 0;
}
.next-callout {
  border-left: 5px solid #4f7cff;
  background: rgba(79,124,255,.12);
  padding: .85rem 1rem;
  border-radius: .75rem;
  margin: .75rem 0;
}
.warn-callout {
  border-left: 5px solid #d29922;
  background: rgba(210,153,34,.13);
  padding: .85rem 1rem;
  border-radius: .75rem;
  margin: .75rem 0;
}
.small-muted {font-size:.88rem; color:var(--orphee-text-muted);}
div[data-testid="stTextArea"] textarea {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  font-size: .88rem;
  line-height: 1.55;
  border-radius: .7rem;
}
div[data-testid="stDownloadButton"] > button, div[data-testid="stButton"] > button {border-radius: .75rem;}
@media (max-width: 900px) {.step-grid {grid-template-columns: 1fr;}}
</style>
""",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# État
# ─────────────────────────────────────────────────────────────────────────────

def init_state() -> None:
    defaults = {
        "ctx": None,
        "title_effective": "",
        "yaourt_text": "",
        "user_instructions": "",
        "prompt1": "",
        "handoff1": "",
        "prompt2": "",
        "handoff2": "",
        "prompt3": "",
        "final_pure": "",
        "audit_report": "",
        "correction_prompt": "",
        "reached_step": 1,
        "links": [
            {"label": "ChatGPT", "url": "https://chat.openai.com"},
            {"label": "Gemini", "url": "https://gemini.google.com"},
        ],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


def filename(prefix: str, title: str, suffix: str) -> str:
    return f"{slugify_filename(title or prefix)}_{suffix}.txt"


def context_from_inputs(title_input: str, file_name_title: str, instructions: str, yaourt: str) -> BuildContext:
    if title_input.strip():
        title = title_input.strip().upper()
        title_source = "manual_title"
    elif file_name_title.strip():
        title = file_name_title.strip().upper()
        title_source = "uploaded_filename"
    elif instructions.strip():
        title = "TITLE TO BE DETERMINED BY AI"
        title_source = "no_title_user_instructions_present"
    else:
        title = "TITLE TO BE DETERMINED BY AI"
        title_source = "no_title"
    return build_context(title, title_source, instructions, yaourt)


def set_step(step: int) -> None:
    st.session_state.reached_step = max(int(st.session_state.get("reached_step", 1)), step)


def step_status(step: int) -> str:
    reached = int(st.session_state.get("reached_step", 1))
    if reached > step:
        return "done"
    if reached == step:
        return "open"
    return "locked"


def stepper() -> None:
    steps = [
        (1, "Prompt 1", "Source → Handoff 1"),
        (2, "Prompt 2", "Handoff 1 → Handoff 2"),
        (3, "Prompt 3", "Handoff 2 → texte final"),
        (4, "Audit", "Texte final → corrections"),
    ]
    html = ['<div class="step-grid">']
    for num, title, desc in steps:
        status = step_status(num)
        icon = "✅" if status == "done" else ("●" if status == "open" else "○")
        html.append(
            f'<div class="step-pill {status}"><div class="step-num">{icon} Étape {num}</div>'
            f'<div class="step-title">{title}</div><div class="step-desc">{desc}</div></div>'
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def copy_action(text: str, button_label: str, key: str, guidance: str, color: str = "#2563eb") -> None:
    """Bouton copier avec message d'étape suivant affiché côté navigateur."""
    payload = json.dumps(text)
    guidance_payload = json.dumps(guidance)
    button_payload = json.dumps(button_label)
    safe_key = "copy_" + "".join(ch if ch.isalnum() else "_" for ch in key)
    components.html(
        f"""
<div style="margin:.25rem 0 .75rem 0;">
  <button id="{safe_key}_btn" style="
      background:{color}; color:white; border:0; border-radius:11px;
      padding:.62rem 1rem; font-weight:800; font-size:.94rem;
      cursor:pointer; box-shadow:0 1px 2px rgba(0,0,0,.12);">
      {button_label}
  </button>
  <div id="{safe_key}_msg" style="display:none; margin-top:.65rem; padding:.72rem .85rem;
      border-radius:12px; background:rgba(34,160,107,.14); border:1px solid rgba(34,160,107,.35);
      font-family:system-ui,-apple-system,Segoe UI,sans-serif; font-size:.92rem; line-height:1.45;">
  </div>
</div>
<script>
const payload_{safe_key} = {payload};
const guidance_{safe_key} = {guidance_payload};
const defaultLabel_{safe_key} = {button_payload};
const btn_{safe_key} = document.getElementById('{safe_key}_btn');
const msg_{safe_key} = document.getElementById('{safe_key}_msg');
btn_{safe_key}.onclick = async () => {{
  try {{
    await navigator.clipboard.writeText(payload_{safe_key});
    btn_{safe_key}.innerText = '✅ Copié dans le presse-papier';
    msg_{safe_key}.innerHTML = guidance_{safe_key};
    msg_{safe_key}.style.display = 'block';
    setTimeout(() => {{ btn_{safe_key}.innerText = defaultLabel_{safe_key}; }}, 2800);
  }} catch (err) {{
    btn_{safe_key}.innerText = '❌ Copie impossible — sélectionnez le texte manuellement';
    msg_{safe_key}.innerHTML = 'Le navigateur a bloqué l’accès au presse-papier. Sélectionnez le texte dans la boîte et copiez-le manuellement.';
    msg_{safe_key}.style.display = 'block';
  }}
}};
</script>
""",
        height=120,
    )


def result_box(title: str, text: str, copy_label: str, copy_key: str, guidance: str, color: str, download_suffix: str) -> None:
    st.markdown(f"### {title}")
    copy_action(text, copy_label, copy_key, guidance, color=color)
    with st.expander("Afficher / vérifier le texte complet", expanded=False):
        st.text_area(title, value=text, height=430, key=f"text_{copy_key}", label_visibility="collapsed")
    st.download_button(
        "⬇️ Télécharger le fichier .txt",
        data=text,
        file_name=filename("orphee", st.session_state.title_effective, download_suffix),
        mime="text/plain",
        use_container_width=True,
        key=f"dl_{copy_key}",
    )


def locked_card(title: str, message: str) -> None:
    st.markdown(
        f"""
<div class="card" style="opacity:.63;">
  <h3>{title}</h3>
  <p class="small-muted">{message}</p>
</div>
""",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Barre latérale
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Raccourcis")
    for link in st.session_state.links:
        st.link_button(link["label"], link["url"], use_container_width=True)

    with st.expander("Gérer les liens IA"):
        new_label = st.text_input("Nom", key="new_link_label", placeholder="Ex. Claude, Mistral, Copilot")
        new_url = st.text_input("URL", key="new_link_url", placeholder="https://…")
        if st.button("Ajouter", use_container_width=True):
            if new_label.strip() and new_url.strip():
                st.session_state.links.append({"label": new_label.strip(), "url": new_url.strip()})
                st.rerun()
            st.warning("Ajoutez un nom et une URL.")
        if st.session_state.links:
            idx = st.selectbox(
                "Supprimer un lien",
                range(len(st.session_state.links)),
                format_func=lambda i: st.session_state.links[i]["label"],
            )
            if st.button("Supprimer", use_container_width=True):
                st.session_state.links.pop(idx)
                st.rerun()

    st.divider()
    if st.button("Réinitialiser la session", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# En-tête
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(
    f"""
<div class="orphee-hero">
  <p class="orphee-title">🎵 ORPHÉE</p>
  <p class="orphee-sub">Interface guidée · {APP_VERSION} · Prompt 1 → Prompt 2 → Prompt 3 → Audit final</p>
</div>
""",
    unsafe_allow_html=True,
)

stepper()

st.markdown(
    """
<div class="next-callout">
<b>Mode d’emploi express :</b> générez le Prompt 1, copiez-le dans votre agent IA, puis revenez coller le Handoff 1 généré. L’interface ouvrira ensuite l’étape suivante. Oui, enfin une app qui ne suppose pas que vous avez une mémoire de pieuvre augmentée.
</div>
""",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# Étape 1
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="card card-soft">', unsafe_allow_html=True)
st.markdown("### 1. Créer le Prompt 1")
st.markdown('<p class="small-muted">Commencez avec un yaourt/source, un titre, des instructions, ou une combinaison des trois.</p>', unsafe_allow_html=True)

col_title, col_mode = st.columns([1, 1])
with col_title:
    title_input = st.text_input("Titre", placeholder="Laisser vide si l’IA doit le choisir", key="title_input")
with col_mode:
    source_mode_choice = st.radio(
        "Source de départ",
        ["Coller le texte", "Téléverser .txt", "Aucun yaourt / mode libre"],
        horizontal=True,
        key="source_mode_radio",
    )

instructions = st.text_area(
    "Instructions facultatives",
    value=st.session_state.user_instructions,
    height=105,
    placeholder="Ex. ton plus cru, éviter les métaphores urbaines, relation non romantique, thème honte familiale…",
    key="instructions_box",
)

yaourt = ""
file_title = ""
if source_mode_choice == "Coller le texte":
    yaourt = st.text_area(
        "Yaourt / texte source avec sections entre crochets",
        value=st.session_state.yaourt_text,
        height=250,
        placeholder="[VERSE]\nda DUM da da DUM\n...\n\n[CHORUS]\nda DUM da DUM",
        key="yaourt_box",
    )
elif source_mode_choice == "Téléverser .txt":
    uploaded = st.file_uploader("Téléverser un fichier .txt", type=["txt"], key="source_upload")
    if uploaded:
        yaourt = uploaded.read().decode("utf-8", errors="replace")
        file_title = normalize_title_from_filename(uploaded.name)
        st.info(f"Titre extrait du fichier : {file_title}")
        with st.expander("Aperçu du texte importé", expanded=True):
            st.text_area("Aperçu", value=yaourt, height=220, disabled=True, label_visibility="collapsed")
else:
    st.markdown(
        """
<div class="warn-callout">
<b>Mode libre :</b> aucun blueprint local ne sera créé. Prompt 1 choisira la structure, la longueur et la métrique interne selon le titre et/ou les instructions.
</div>
""",
        unsafe_allow_html=True,
    )

if st.button("🎵 Générer le Prompt 1", type="primary", use_container_width=True, key="generate_p1"):
    if not (title_input.strip() or instructions.strip() or yaourt.strip()):
        st.error("Ajoutez au moins un titre, des instructions ou un yaourt/source.")
        st.stop()
    try:
        ctx = context_from_inputs(title_input, file_title, instructions, yaourt)
        prompt1 = assembler_prompt_1(ctx)
        st.session_state.ctx = ctx
        st.session_state.title_effective = ctx.title
        st.session_state.yaourt_text = yaourt
        st.session_state.user_instructions = instructions
        st.session_state.prompt1 = prompt1
        set_step(2)
        st.success(f"Prompt 1 généré — Mode : {ctx.source_mode} · Langue : {ctx.language} · Lignes : {ctx.row_count if ctx.rows else 'structure libre'}")
    except Exception as exc:
        st.error(f"Erreur pendant la génération du Prompt 1 : {exc}")
        st.exception(exc)

st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.prompt1:
    result_box(
        title="Prompt 1 prêt",
        text=st.session_state.prompt1,
        copy_label="📋 Copier le Prompt 1",
        copy_key="p1",
        color="#2563eb",
        download_suffix="PROMPT_1_SOURCE_v1_2",
        guidance=(
            "<b>Prompt 1 copié.</b><br>Collez-le maintenant dans le chat de votre agent IA. "
            "Quand l’agent aura généré le <b>Handoff 1</b>, revenez ici et collez ce Handoff dans la boîte de l’étape 2, puis cliquez sur <b>Générer le Prompt 2</b>."
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Étape 2
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.prompt1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 2. Coller le Handoff 1 et créer le Prompt 2")
    st.markdown('<p class="small-muted">Collez ici le Handoff 1 complet produit par l’agent IA après le Prompt 1.</p>', unsafe_allow_html=True)
    handoff1 = st.text_area(
        "Handoff 1",
        value=st.session_state.handoff1,
        height=230,
        placeholder="Collez ici le Handoff 1…",
        key="handoff1_box",
    )
    if st.button("🎼 Générer le Prompt 2", type="primary", use_container_width=True, key="generate_p2"):
        if not handoff1.strip():
            st.error("Collez le Handoff 1 avant de générer le Prompt 2.")
            st.stop()
        ctx = st.session_state.ctx
        if ctx is None:
            ctx = build_context(st.session_state.title_effective or "TITLE TO BE DETERMINED BY AI", "session_rebuild", st.session_state.user_instructions, st.session_state.yaourt_text)
            st.session_state.ctx = ctx
        try:
            prompt2 = assembler_prompt_2(ctx, handoff1)
            st.session_state.handoff1 = handoff1
            st.session_state.prompt2 = prompt2
            set_step(3)
            st.success("Prompt 2 généré.")
        except Exception as exc:
            st.error(f"Erreur pendant la génération du Prompt 2 : {exc}")
            st.exception(exc)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.prompt2:
        result_box(
            title="Prompt 2 prêt",
            text=st.session_state.prompt2,
            copy_label="📋 Copier le Prompt 2",
            copy_key="p2",
            color="#7c3aed",
            download_suffix="PROMPT_2_TOPLINER_v1_0",
            guidance=(
                "<b>Prompt 2 copié.</b><br>Collez-le dans le chat de votre agent IA. "
                "Quand l’agent aura généré le <b>Handoff 2</b>, revenez ici et collez ce Handoff dans l’étape 3, puis cliquez sur <b>Générer le Prompt 3</b>."
            ),
        )
else:
    locked_card("2. Prompt 2", "Générez d’abord le Prompt 1. L’étape suivante s’ouvrira ensuite automatiquement.")


# ─────────────────────────────────────────────────────────────────────────────
# Étape 3
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.prompt2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 3. Coller le Handoff 2 et créer le Prompt 3")
    st.markdown('<p class="small-muted">Collez ici le Handoff 2 complet produit par l’agent IA après le Prompt 2.</p>', unsafe_allow_html=True)
    handoff2 = st.text_area(
        "Handoff 2",
        value=st.session_state.handoff2,
        height=230,
        placeholder="Collez ici le Handoff 2…",
        key="handoff2_box",
    )
    if st.button("🎚️ Générer le Prompt 3", type="primary", use_container_width=True, key="generate_p3"):
        if not handoff2.strip():
            st.error("Collez le Handoff 2 avant de générer le Prompt 3.")
            st.stop()
        ctx = st.session_state.ctx
        if ctx is None:
            ctx = build_context(st.session_state.title_effective or "TITLE TO BE DETERMINED BY AI", "session_rebuild", st.session_state.user_instructions, st.session_state.yaourt_text)
            st.session_state.ctx = ctx
        try:
            prompt3 = assembler_prompt_3(ctx, handoff2)
            st.session_state.handoff2 = handoff2
            st.session_state.prompt3 = prompt3
            set_step(4)
            st.success("Prompt 3 généré.")
        except Exception as exc:
            st.error(f"Erreur pendant la génération du Prompt 3 : {exc}")
            st.exception(exc)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.prompt3:
        result_box(
            title="Prompt 3 prêt",
            text=st.session_state.prompt3,
            copy_label="📋 Copier le Prompt 3",
            copy_key="p3",
            color="#0f766e",
            download_suffix="PROMPT_3_FINALIZER_v1_0",
            guidance=(
                "<b>Prompt 3 copié.</b><br>Collez-le dans le chat de votre agent IA. "
                "À la fin, copiez le bloc <b>FINAL HANDOFF — PURE LYRICS ONLY</b> s’il apparaît seul. Si l’agent vous renvoie toute la sortie, collez-la quand même à l’étape 4 : l’app extraira le bloc pur automatiquement."
            ),
        )
else:
    locked_card("3. Prompt 3", "Générez d’abord le Prompt 2. L’étape finale s’ouvrira ensuite.")


# ─────────────────────────────────────────────────────────────────────────────
# Étape 4 — Audit
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.prompt3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 4. Auditer le texte final")
    st.markdown(
        '<p class="small-muted">Collez le bloc final pur OU toute la sortie Prompt 3. L’app extrait automatiquement le bloc “FINAL HANDOFF — PURE LYRICS ONLY”, même sans lignes vides entre les sections.</p>',
        unsafe_allow_html=True,
    )

    with st.expander("Option : extraire manuellement depuis une sortie complète Prompt 3"):
        full_output = st.text_area(
            "Sortie complète Prompt 3",
            height=230,
            placeholder="Collez ici la sortie complète, puis cliquez sur Extraire le bloc pur…",
            key="full_p3_output_box",
        )
        if st.button("Extraire le bloc pur depuis cette sortie", use_container_width=True, key="extract_pure"):
            st.session_state.final_pure = extract_final_pure_lyrics(full_output)
            st.success("Bloc pur extrait et normalisé. Vérifiez-le dans la boîte d’audit ci-dessous.")

    final_text = st.text_area(
        "Texte final pur",
        value=st.session_state.final_pure,
        height=285,
        placeholder="[VERSE] #1\nligne\nligne\n\n[CHORUS] #1\nligne\nligne",
        key="final_pure_box",
    )

    if st.button("🔍 Auditer le texte final", type="primary", use_container_width=True, key="audit_final"):
        ctx = st.session_state.ctx
        rows = ctx.rows if ctx is not None else []
        if not final_text.strip():
            st.error("Collez le texte final pur avant de lancer l’audit.")
            st.stop()
        try:
            clean_final_text = extract_final_pure_lyrics(final_text)
            report, issues = audit_final_text(clean_final_text, rows)
            correction = build_correction_prompt(report, clean_final_text)
            st.session_state.final_pure = clean_final_text
            st.session_state.audit_report = report
            st.session_state.correction_prompt = correction
            if issues:
                st.warning(f"Audit terminé : {len(issues)} problème(s) détecté(s).")
            else:
                st.success("Audit terminé : aucun problème critique détecté.")
        except Exception as exc:
            st.error(f"Erreur pendant l’audit : {exc}")
            st.exception(exc)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.audit_report:
        result_box(
            title="Rapport d’audit prêt",
            text=st.session_state.audit_report,
            copy_label="📋 Copier le rapport d’audit",
            copy_key="audit_report",
            color="#b45309",
            download_suffix="AUDIT_FINAL",
            guidance=(
                "<b>Rapport copié.</b><br>Conservez-le pour diagnostiquer les écarts. "
                "Si des corrections sont nécessaires, copiez aussi le prompt de correction ci-dessous et collez-le dans l’agent IA qui a généré le dernier texte."
            ),
        )
        result_box(
            title="Prompt de correction prêt",
            text=st.session_state.correction_prompt,
            copy_label="📋 Copier le prompt de correction",
            copy_key="correction_prompt",
            color="#be123c",
            download_suffix="PROMPT_CORRECTION_AUDIT",
            guidance=(
                "<b>Prompt de correction copié.</b><br>Collez-le dans le chat de l’agent IA qui a produit le dernier texte final. "
                "Il devra corriger seulement les lignes rejetées, sans toucher aux lignes conformes. Oui, une discipline révolutionnaire."
            ),
        )
else:
    locked_card("4. Auditeur final", "Générez d’abord le Prompt 3. L’auditeur apparaîtra ensuite.")


# ─────────────────────────────────────────────────────────────────────────────
# Diagnostic avancé
# ─────────────────────────────────────────────────────────────────────────────

with st.expander("Diagnostic avancé / blueprint", expanded=False):
    ctx = st.session_state.ctx
    if ctx is None:
        st.info("Aucun contexte généré pour l’instant.")
    else:
        st.write(f"**Titre :** {ctx.title}")
        st.write(f"**Langue :** {ctx.language}")
        st.write(f"**Mode :** {ctx.source_mode}")
        st.write(f"**Nombre de lignes blueprint :** {ctx.row_count if ctx.rows else 'N/A'}")
        st.text_area("Blueprint complet", value=ctx.blueprint_full, height=260, label_visibility="collapsed")
        st.download_button(
            "Télécharger le blueprint complet",
            data=ctx.blueprint_full,
            file_name=filename("orphee", ctx.title, "BLUEPRINT_FULL"),
            mime="text/plain",
            use_container_width=True,
        )
