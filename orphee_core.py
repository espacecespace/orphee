# -*- coding: utf-8 -*-
"""
ORPHÉE v8.5 — Core
======================
Fonctions communes pour l'interface Streamlit locale :
- analyse acoustique du yaourt/source,
- assemblage des trois prompts,
- extraction du bloc final pur,
- audit local final,
- génération d'un prompt de correction.

Le module évite les dépendances à l'ancien système de dossiers parent/enfant.
Tout se fait en mémoire depuis l'interface. Une bénédiction rare dans le monde
du tooling maison, ce petit théâtre où les chemins relatifs deviennent des démons.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

ROOT = Path(__file__).resolve().parent
GABARITS_DIR = ROOT  # Version GitHub simplifiée : gabarits à la racine, aucun sous-dossier

SOURCE_P1_TEMPLATE = "ORPHEE_SOURCE_PROMPT_1_v1_2_FINAL.txt"
TOPLINER_P2_TEMPLATE = "ORPHEE_TOPLINER_PROMPT_2_v1_0_FINAL.txt"
FINALIZER_P3_TEMPLATE = "ORPHEE_FINALIZER_PROMPT_3_v1_0_FINAL.txt"
AUDIT_CORRECTION_TEMPLATE = "ORPHEE_AUDIT_CORRECTION_v1_0.txt"

SOURCE_ZONE_RE = re.compile(r"°#x#°0°.*?°#x#°9°", re.DOTALL)
BLUEPRINT_ZONE_RE = re.compile(r"°#b#°0°.*?°#b#°9°", re.DOTALL)
HANDOFF_ZONE_RE = re.compile(r"°#h#°0°.*?°#h#°9°", re.DOTALL)
SECTION_TAG_RE = re.compile(r"^\s*\[([A-Za-zÀ-ÿ0-9 _\-]+)\](?:\s*#\s*(\d+))?\s*$")
INLINE_COMMENT_RE = re.compile(r"\(.*?\)")


# Mots faibles à éviter sur une attaque forte / note tenue.
# Ce n'est pas une grammaire parfaite, c'est un garde-fou musical local.
HARD_WEAK_ATTACK_WORDS = {
    "the", "a", "an", "of", "to", "for", "from", "in", "on", "at", "by", "as",
    "than", "with", "into", "onto", "over", "under", "through", "about", "around",
    "per", "via", "up", "out", "off",
}
SOFT_WEAK_ATTACK_WORDS = {
    "am", "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "have", "has", "had",
    "will", "would", "can", "could", "should", "may", "might", "must",
    "i", "you", "he", "she", "we", "they", "it", "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their", "that", "this", "these", "those",
    "and", "or", "but", "if", "so", "yet",
}
WORD_RE = re.compile(r"[A-Za-zÀ-ÿ']+")

TITLE_PLACEHOLDERS = [
    "[TITRE_DE_LA_CHANSON_AUTOMATIQUE]",
    "{{TITLE}}",
    "{{SONG_TITLE}}",
]
LANGUAGE_PLACEHOLDERS = [
    "[LANGUE_DÉTÉCTÉE]",
    "[LANGUE_DÉTECTÉE]",
    "{{LANGUAGE}}",
    "{{DETECTED_LANGUAGE}}",
]
SESSION_MEMORY_PLACEHOLDERS = [
    "[Declare previous-session exclusions here, or write: SESSION 1 — no prior exclusions.]",
    "{{SESSION_MEMORY}}",
]
OPTIONAL_EXCLUSION_PLACEHOLDERS = [
    "[Optional: territory, setting, bond type, object-function, emotional mechanism to avoid. If blank, default anti-generic rules apply.]",
    "{{OPTIONAL_USER_EXCLUSION}}",
]
EXPECTED_HANDOFF_PLACEHOLDERS = [
    "{{EXPECTED_HANDOFF_SOURCE_VERSION}}",
    "[EXPECTED_HANDOFF_SOURCE_VERSION]",
]


@dataclass
class BlueprintRow:
    row_id: int
    section: str
    partition: str
    total: int
    stress: str
    rhyme: str
    source_line: str


@dataclass
class BuildContext:
    title: str
    title_source: str
    language: str
    user_instructions: str
    source_mode: str
    yaourt: str
    source_package: str
    blueprint_full: str
    blueprint_reduced: str
    rows: list[BlueprintRow]
    row_count: int
    section_signature: list[str]


@dataclass
class AuditIssue:
    severity: str
    row_id: Optional[int]
    section: str
    message: str
    current_line: str = ""
    expected: str = ""
    observed: str = ""


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_template(name: str) -> str:
    path = GABARITS_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Gabarit introuvable : {path}. Dans la version FLAT, tous les fichiers .txt de gabarit doivent être à la racine du repo, à côté de app.py.")
    return load_text(path)


def replace_all(text: str, placeholders: Iterable[str], value: str) -> str:
    for ph in placeholders:
        text = text.replace(ph, value)
    return text


def slugify_filename(text: str) -> str:
    s = text.strip().lower()
    repl = {
        "à": "a", "â": "a", "ä": "a", "á": "a", "ã": "a", "å": "a",
        "ç": "c", "è": "e", "é": "e", "ê": "e", "ë": "e",
        "ì": "i", "í": "i", "î": "i", "ï": "i",
        "ò": "o", "ó": "o", "ô": "o", "ö": "o", "õ": "o",
        "ù": "u", "ú": "u", "û": "u", "ü": "u",
        "ý": "y", "ÿ": "y", "ñ": "n", "œ": "oe", "æ": "ae",
    }
    for a, b in repl.items():
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "untitled"


def normalize_title_from_filename(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"[_\-]+", " ", stem).strip()
    stem = re.sub(r"\s+", " ", stem)
    return stem.upper() if stem else "CHANSON SANS TITRE"


def is_section_tag(line: str) -> tuple[bool, Optional[str]]:
    s = line.strip()
    m = SECTION_TAG_RE.match(s)
    if not m:
        return False, None
    label = m.group(1).strip().upper()
    idx = m.group(2)
    if idx:
        return True, f"[{label}] #{idx}"
    return True, f"[{label}]"


def canonical_section_base(section: str) -> str:
    s = section.strip().upper()
    s = re.sub(r"\s*#\s*\d+\s*$", "", s)
    return s


def detect_language(text: str) -> str:
    fr_markers = r"\b(le|la|les|un|une|des|du|de|et|ou|dans|je|tu|il|elle|nous|vous|mon|ma|mes|ton|ta|tes|sur|pour|avec|mais|quand|comme|ça|c'est|j'ai|t'es|même|plus|pas|ne|que|qui)\b"
    en_markers = r"\b(the|a|an|and|or|in|on|at|to|of|for|with|but|when|as|i|you|he|she|we|they|my|your|our|is|are|was|were|have|has|don't|can't|not|that|this)\b"
    fr = len(re.findall(fr_markers, text, re.I))
    en = len(re.findall(en_markers, text, re.I))
    return "FRANÇAIS" if fr > en * 1.2 else "ENGLISH"


def load_phonetic_engine() -> Callable[[str], dict]:
    try:
        from moteur_phonetique import analyser_ADN_phonetique  # type: ignore
        return analyser_ADN_phonetique
    except Exception:
        def fallback(line: str) -> dict:
            # Dernier filet de sécurité : très approximatif. L'interface signale que
            # le moteur local est à vérifier. Mieux qu'un crash, moins glorieux qu'un vrai moteur.
            words = re.findall(r"[A-Za-zÀ-ÿ']+", line)
            count = sum(max(1, len(re.findall(r"[aeiouyAEIOUYàâäéèêëîïôöùûü]+", w))) for w in words)
            return {"count": count, "stress_pattern": "", "end_rhyme": "-"}
        return fallback


def escape_md_cell(text: str) -> str:
    text = text.strip().replace("|", "/")
    text = re.sub(r"\s+", " ", text)
    return text


def analyze_line(line: str, analyzer: Callable[[str], dict]) -> tuple[str, int, str, str]:
    clean_calc = INLINE_COMMENT_RE.sub("", line).strip() or line.strip()
    segments = re.split(r"([,;\-\.\!\?])", clean_calc)
    partitions: list[str] = []
    stresses: list[str] = []
    total = 0
    end_rhyme = ""
    buffer = ""

    for seg in segments:
        if seg in [",", ";", "-", ".", "!", "?"]:
            if buffer.strip():
                adn = analyzer(buffer.strip()) or {}
                cnt = int(adn.get("count") or 0)
                partitions.append(f"[{cnt}]")
                total += cnt
                if adn.get("stress_pattern"):
                    stresses.append(str(adn.get("stress_pattern")))
                if adn.get("end_rhyme"):
                    end_rhyme = str(adn.get("end_rhyme"))
                buffer = ""
        else:
            buffer += seg

    if buffer.strip():
        adn = analyzer(buffer.strip()) or {}
        cnt = int(adn.get("count") or 0)
        partitions.append(f"[{cnt}]")
        total += cnt
        if adn.get("stress_pattern"):
            stresses.append(str(adn.get("stress_pattern")))
        if adn.get("end_rhyme"):
            end_rhyme = str(adn.get("end_rhyme"))

    return " + ".join(partitions) if partitions else "[0]", total, " / ".join(stresses), end_rhyme or "-"




def flatten_stress_pattern(pattern: str) -> list[str]:
    """Retourne une liste de DUM/da, sans les séparateurs de segments."""
    return re.findall(r"\b(?:DUM|da)\b", pattern or "")


def classify_attack_word(word: str) -> str:
    w = word.lower().strip("'’`.,;:!?()[]{}\"")
    if w in HARD_WEAK_ATTACK_WORDS:
        return "HARD_WEAK"
    if w in SOFT_WEAK_ATTACK_WORDS or w.endswith("n't") or w.endswith("'s") or w.endswith("'d") or w.endswith("'ll"):
        return "SOFT_WEAK"
    return "CONTENT"


def syllable_word_profile(line: str, analyzer: Callable[[str], dict]) -> list[dict]:
    """
    Approxime l'alignement syllabe -> mot.
    Sert à repérer les attaques fortes placées sur des mots faibles.
    """
    clean = INLINE_COMMENT_RE.sub("", line).strip() or line.strip()
    profile: list[dict] = []
    for match in WORD_RE.finditer(clean):
        word = match.group(0)
        try:
            adn = analyzer(word) or {}
            count = int(adn.get("count") or 0)
        except Exception:
            count = 0
        if count <= 0:
            count = 1
        stress_tokens = flatten_stress_pattern(str((adn or {}).get("stress_pattern") or ""))
        if len(stress_tokens) < count:
            # Fallback conservateur : contenu = première syllabe forte, fonction = faible.
            default = "DUM" if classify_attack_word(word) == "CONTENT" else "da"
            stress_tokens = stress_tokens + [default] * (count - len(stress_tokens))
        for syll_idx in range(count):
            profile.append({
                "word": word,
                "class": classify_attack_word(word),
                "word_syllable_index": syll_idx + 1,
                "stress": stress_tokens[syll_idx] if syll_idx < len(stress_tokens) else "",
            })
    return profile


def audit_strong_attack_alignment(row: BlueprintRow, candidate_line: str, analyzer: Callable[[str], dict]) -> tuple[list[str], list[str]]:
    """
    Détecte les attaques fortes / syllabes porteuses mal remplacées.
    Exemple rejeté : source 'Lo-' sur DUM -> candidat 'The' sur la même position.
    Retourne (erreurs_fatales, avertissements).
    """
    target_stress = flatten_stress_pattern(row.stress)
    if not target_stress:
        return [], []
    source_profile = syllable_word_profile(row.source_line, analyzer)
    cand_profile = syllable_word_profile(candidate_line, analyzer)
    n = min(len(target_stress), len(source_profile), len(cand_profile))
    errors: list[str] = []
    warnings: list[str] = []
    for pos in range(n):
        if target_stress[pos] != "DUM":
            continue
        src = source_profile[pos]
        cand = cand_profile[pos]
        # Attaque forte source porteuse remplacée par article/préposition faible : fail local.
        if src["class"] == "CONTENT" and cand["class"] == "HARD_WEAK":
            errors.append(
                f"syllabe {pos+1}: attaque forte source '{src['word']}' remplacée par mot faible '{cand['word']}'"
            )
        # Moins fatal, mais musicalement suspect : auxiliaire/pronom/conjonction sur position forte.
        elif src["class"] == "CONTENT" and cand["class"] == "SOFT_WEAK" and cand.get("stress") == "da":
            warnings.append(
                f"syllabe {pos+1}: attaque forte source '{src['word']}' tombe sur mot faible/peu porteur '{cand['word']}'"
            )
    return errors, warnings

def analyze_yaourt(yaourt: str, analyzer: Optional[Callable[[str], dict]] = None) -> tuple[str, str, str, list[BlueprintRow], list[str]]:
    analyzer = analyzer or load_phonetic_engine()
    rows: list[BlueprintRow] = []
    source_pkg = ["| # | Section | Target | Source Line |", "|---|---|:---:|---|"]
    full = ["| # | Section | PARTITION | Total | Rythme (Stress) | Rime Fin | Source Line |", "|---|---|---|:---:|---|---|---|"]
    reduced = ["| # | Section | Total |", "|---|---|:---:|"]

    section_counts: dict[str, int] = {}
    current_section = "[INTRO] #1"
    section_signature: list[str] = []
    row_id = 1

    for raw in yaourt.splitlines():
        clean = raw.strip()
        if not clean:
            continue
        is_tag, tag = is_section_tag(clean)
        if is_tag and tag:
            base = canonical_section_base(tag)
            count = section_counts.get(base, 0) + 1
            section_counts[base] = count
            current_section = f"{base} #{count}"
            section_signature.append(current_section)
            continue

        partition, total, stress, rhyme = analyze_line(clean, analyzer)
        safe = escape_md_cell(clean)
        source_pkg.append(f"| {row_id} | {current_section} | {total} | {safe} |")
        full.append(f"| {row_id} | {current_section} | {partition} | {total} | {escape_md_cell(stress)} | {escape_md_cell(rhyme)} | {safe} |")
        reduced.append(f"| {row_id} | {current_section} | {total} |")
        rows.append(BlueprintRow(row_id, current_section, partition, total, stress, rhyme, clean))
        row_id += 1

    return "\n".join(source_pkg), "\n".join(full), "\n".join(reduced), rows, section_signature


def detect_source_mode(yaourt: str, title: str, instructions: str) -> str:
    return "LOCKED_SOURCE" if yaourt.strip() else "FREE_STRUCTURE"


def build_context(title: str, title_source: str, instructions: str, yaourt: str) -> BuildContext:
    title = title.strip().upper() if title.strip() else "TITLE TO BE DETERMINED BY AI"
    instructions = instructions.strip()
    mode = detect_source_mode(yaourt, title, instructions)

    if mode == "LOCKED_SOURCE":
        source_package, blueprint_full, blueprint_reduced, rows, section_signature = analyze_yaourt(yaourt)
        flat = " ".join(l.strip() for l in yaourt.splitlines() if l.strip() and not is_section_tag(l.strip())[0])
        language = detect_language(f"{title}\n{instructions}\n{flat}")
    else:
        rows = []
        section_signature = []
        blueprint_full = (
            "NO LOCAL SOURCE BLUEPRINT PROVIDED.\n"
            "FREE_STRUCTURE MODE ACTIVE.\n"
            "Prompt 1 must create its own section structure, row count, meter map, and handoff blueprint.\n"
            "Prompt 2 and Prompt 3 must preserve the generated structure from the previous handoff."
        )
        blueprint_reduced = blueprint_full
        source_package = (
            "NO LOCAL YAOURT PROVIDED.\n"
            "FREE_STRUCTURE MODE ACTIVE.\n"
            "The AI may choose the section structure, row count, length, and internal meter.\n"
            "If no title is provided, the AI may propose the title.\n"
            "Any user creative instructions below override title implications if they conflict."
        )
        language = detect_language(f"{title}\n{instructions}") if (title.strip() or instructions.strip()) else "ENGLISH"

    return BuildContext(
        title=title,
        title_source=title_source,
        language=language,
        user_instructions=instructions,
        source_mode=mode,
        yaourt=yaourt,
        source_package=source_package,
        blueprint_full=blueprint_full,
        blueprint_reduced=blueprint_reduced,
        rows=rows,
        row_count=len(rows),
        section_signature=section_signature,
    )


def metadata_block(ctx: BuildContext, stage: str, expected_handoff_version: str = "") -> str:
    instructions = ctx.user_instructions or "No additional user instructions."
    return f"""
══════════════════════════════════════════════════════════
LOCAL INTERFACE METADATA — {stage}
══════════════════════════════════════════════════════════
SONG TITLE FIELD: {ctx.title}
TITLE SOURCE: {ctx.title_source}
DETECTED LANGUAGE: {ctx.language}
SOURCE MODE: {ctx.source_mode}
LOCAL BLUEPRINT ROW COUNT: {ctx.row_count if ctx.rows else 'N/A — FREE_STRUCTURE'}
EXPECTED HANDOFF SOURCE VERSION: {expected_handoff_version or 'N/A'}

USER CREATIVE OVERRIDE / OPTIONAL INSTRUCTIONS:
{instructions}

PRIORITY RULE:
If the optional instructions conflict with the title, follow the optional instructions and reinterpret or downgrade the title.
If no yaourt/source is provided, free-structure mode is active and the AI may choose structure, row count, length, and internal blueprint.
""".strip()


def inject_zone(template: str, regex: re.Pattern, open_tag: str, close_tag: str, content: str) -> str:
    replacement = f"{open_tag}\n{content.strip()}\n{close_tag}"
    if regex.search(template):
        return regex.sub(replacement, template)
    return f"{replacement}\n\n{template}"


def apply_common_replacements(template: str, ctx: BuildContext, optional_exclusion: Optional[str] = None, expected_handoff: str = "") -> str:
    instructions_for_placeholder = optional_exclusion if optional_exclusion is not None else (ctx.user_instructions or "No additional user exclusion. Apply default anti-generic rules.")
    out = template
    out = replace_all(out, TITLE_PLACEHOLDERS, ctx.title)
    out = replace_all(out, LANGUAGE_PLACEHOLDERS, ctx.language)
    out = replace_all(out, SESSION_MEMORY_PLACEHOLDERS, "SESSION 1 — local interface session. Use pasted handoffs as authoritative continuity.")
    out = replace_all(out, OPTIONAL_EXCLUSION_PLACEHOLDERS, instructions_for_placeholder)
    out = replace_all(out, EXPECTED_HANDOFF_PLACEHOLDERS, expected_handoff)
    return out


def assembler_prompt_1(ctx: BuildContext) -> str:
    tpl = load_template(SOURCE_P1_TEMPLATE)
    tpl = apply_common_replacements(tpl, ctx)
    pre = metadata_block(ctx, "PROMPT 1 / SOURCE", "ORPHÉE-SOURCE Prompt 1 v1.2 final")
    package = f"{pre}\n\nSOURCE / BLUEPRINT PACKAGE:\n{ctx.source_package}"
    return inject_zone(tpl, SOURCE_ZONE_RE, "°#x#°0°", "°#x#°9°", package)


def assembler_prompt_2(ctx: BuildContext, handoff1: str) -> str:
    tpl = load_template(TOPLINER_P2_TEMPLATE)
    expected = "ORPHÉE-SOURCE Prompt 1 v1.2 final"
    tpl = apply_common_replacements(tpl, ctx, expected_handoff=expected)
    pre = metadata_block(ctx, "PROMPT 2 / TOPLINER", expected)
    blueprint = f"{pre}\n\nFULL ACOUSTIC BLUEPRINT OR FREE-STRUCTURE NOTICE:\n{ctx.blueprint_full}"
    out = inject_zone(tpl, BLUEPRINT_ZONE_RE, "°#b#°0°", "°#b#°9°", blueprint)
    out = inject_zone(out, HANDOFF_ZONE_RE, "°#h#°0°", "°#h#°9°", handoff1 or "Paste HANDOFF 1 from ORPHÉE-SOURCE here.")
    return out


def assembler_prompt_3(ctx: BuildContext, handoff2: str) -> str:
    tpl = load_template(FINALIZER_P3_TEMPLATE)
    expected = "ORPHÉE-TOPLINER Prompt 2 v1.0 final"
    tpl = apply_common_replacements(tpl, ctx, expected_handoff=expected)
    pre = metadata_block(ctx, "PROMPT 3 / FINALIZER", expected)
    blueprint = f"{pre}\n\nFULL ACOUSTIC BLUEPRINT OR FREE-STRUCTURE NOTICE:\n{ctx.blueprint_full}"
    out = inject_zone(tpl, BLUEPRINT_ZONE_RE, "°#b#°0°", "°#b#°9°", blueprint)
    out = inject_zone(out, HANDOFF_ZONE_RE, "°#h#°0°", "°#h#°9°", handoff2 or "Paste HANDOFF 2 from ORPHÉE-TOPLINER here.")
    return out


def parse_blueprint_table(table: str) -> list[BlueprintRow]:
    rows: list[BlueprintRow] = []
    for line in table.splitlines():
        if not line.strip().startswith("|"):
            continue
        if re.match(r"^\|\s*#\s*\|", line) or "|---" in line:
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) < 7:
            continue
        try:
            row_id = int(cols[0])
            total = int(cols[3])
        except Exception:
            continue
        rows.append(BlueprintRow(row_id, cols[1], cols[2], total, cols[4], cols[5], cols[6]))
    return rows


def parse_pure_lyrics(text: str) -> tuple[list[str], list[str], list[str]]:
    """Retourne (tags, lyric_lines, parasitic_lines_before_first_tag)."""
    tags: list[str] = []
    lyrics: list[str] = []
    parasites: list[str] = []
    seen_tag = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        is_tag, tag = is_section_tag(line)
        if is_tag and tag:
            seen_tag = True
            tags.append(tag)
        else:
            if not seen_tag:
                parasites.append(line)
            else:
                lyrics.append(line)
    return tags, lyrics, parasites


def expected_section_tags(rows: list[BlueprintRow]) -> list[str]:
    tags: list[str] = []
    last = None
    for row in rows:
        if row.section != last:
            tags.append(row.section)
            last = row.section
    return tags


def format_pure_lyrics_block(text: str) -> str:
    """Normalise l'affichage du bloc final : une ligne vide avant chaque nouvelle section."""
    out: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if is_section_tag(line)[0]:
            if out and out[-1] != "":
                out.append("")
            out.append(line)
        else:
            out.append(line)
    return "\n".join(out).strip()


def extract_final_pure_lyrics(model_output: str) -> str:
    """Extrait un bloc paroles pur depuis une sortie complète Prompt 3 ou un bloc déjà pur.

    Robuste aux variantes fréquentes :
    - heading FINAL HANDOFF — PURE LYRICS ONLY;
    - bloc ```text ... ```;
    - absence de lignes vides entre sections;
    - sortie complète collée par erreur dans la boîte d'audit.
    """
    marker = "FINAL HANDOFF — PURE LYRICS ONLY"
    text = model_output.strip()

    if marker in text:
        tail = text.split(marker, 1)[1].strip()
    else:
        # fallback : commence à la première balise section plausible.
        m = re.search(r"(?m)^\s*\[[A-Za-zÀ-ÿ0-9 _\-]+\](?:\s*#\s*\d+)?\s*$", text)
        tail = text[m.start():] if m else text

    # Si un bloc de code suit le heading, ne prendre que son contenu.
    fence = re.search(r"```(?:text|txt|lyrics|markdown)?\s*\n(.*?)\n```", tail, flags=re.S | re.I)
    if fence:
        tail = fence.group(1).strip()

    lines: list[str] = []
    started = False
    for raw in tail.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("```"):
            continue
        is_tag, _ = is_section_tag(line)
        if is_tag:
            started = True
            lines.append(line)
            continue
        if not started:
            # Ignore petites lignes décoratives après le marker avant la première section.
            continue
        # Stopper si un bloc d'audit reprend après le handoff pur.
        if re.match(r"^(SECTION\s+\d+|={5,}|</studio_session>|FINAL STATUS|RAPPORT|MASTER CUT|CHANGELOG)\b", line, flags=re.I):
            break
        lines.append(line)

    return format_pure_lyrics_block("\n".join(lines))


def audit_final_text(final_text: str, blueprint_rows: list[BlueprintRow]) -> tuple[str, list[AuditIssue]]:
    # Accepte une sortie complète Prompt 3 OU un bloc pur.
    final_text = extract_final_pure_lyrics(final_text)
    tags, lyric_lines, parasites = parse_pure_lyrics(final_text)
    issues: list[AuditIssue] = []
    report: list[str] = []
    analyzer = load_phonetic_engine()

    report.append("RAPPORT D’AUDIT FINAL ORPHÉE")
    report.append("=" * 64)

    if not blueprint_rows:
        report.append("MODE AUDIT LÉGER — aucun blueprint strict disponible.")
        report.append(f"Sections détectées : {len(tags)}")
        report.append(f"Lignes paroles détectées : {len(lyric_lines)}")
        for idx, line in enumerate(lyric_lines, 1):
            partition, total, stress, rhyme = analyze_line(line, analyzer)
            report.append(f"#{idx:03d} | {total} syll. | {partition} | {line}")
        return "\n".join(report), issues

    expected_tags = expected_section_tags(blueprint_rows)

    report.append("1. STRUCTURE")
    report.append(f"Sections attendues : {len(expected_tags)}")
    report.append(f"Sections obtenues  : {len(tags)}")
    report.append(f"Lignes attendues   : {len(blueprint_rows)}")
    report.append(f"Lignes obtenues    : {len(lyric_lines)}")

    if parasites:
        msg = "Lignes parasites avant la première section : " + " / ".join(parasites[:5])
        issues.append(AuditIssue("ERROR", None, "GLOBAL", msg))
        report.append("❌ " + msg)

    if tags != expected_tags:
        issues.append(AuditIssue("ERROR", None, "SECTIONS", "Les balises de sections ne correspondent pas exactement.", expected=" | ".join(expected_tags), observed=" | ".join(tags)))
        report.append("❌ Balises de sections : NON CONFORMES")
        max_len = max(len(expected_tags), len(tags))
        for i in range(max_len):
            exp = expected_tags[i] if i < len(expected_tags) else "[ABSENT]"
            obs = tags[i] if i < len(tags) else "[ABSENT]"
            status = "✅" if exp == obs else "❌"
            report.append(f"   {status} Section {i+1}: attendu {exp} | obtenu {obs}")
    else:
        report.append("✅ Balises de sections : CONFORMES")

    if len(lyric_lines) != len(blueprint_rows):
        issues.append(AuditIssue("ERROR", None, "ROW_COUNT", "Nombre de lignes paroles incorrect.", expected=str(len(blueprint_rows)), observed=str(len(lyric_lines))))
        report.append("❌ Nombre de lignes : NON CONFORME")
    else:
        report.append("✅ Nombre de lignes : CONFORME")

    report.append("\n2. MÉTRIQUE / PARTITION / ATTAQUES FORTES")
    report.append("NOTE : la partition est une contrainte dure. Exemple : [2] + [14] ≠ [16], même si le total syllabique est identique.")
    report.append("NOTE : les attaques fortes sont aussi musicales. Une position forte/tenue ne doit pas être déplacée sur un article ou une préposition faible si la source portait un vrai mot.")
    limit = min(len(lyric_lines), len(blueprint_rows))
    fatal_metric = 0
    fatal_attack = 0
    warnings = 0
    for i in range(limit):
        row = blueprint_rows[i]
        line = lyric_lines[i].replace("|", "/")
        partition, total, stress, rhyme = analyze_line(line, analyzer)
        total_ok = total == row.total
        partition_ok = partition == row.partition
        attack_errors, attack_warnings = audit_strong_attack_alignment(row, line, analyzer)
        if total_ok and partition_ok and not attack_errors:
            report.append(f"✅ Row {row.row_id:03d} | {row.section} | OK | {line}")
        else:
            if not (total_ok and partition_ok):
                fatal_metric += 1
            if attack_errors:
                fatal_attack += len(attack_errors)
            msg = f"Row {row.row_id}: métrique / partition / attaque rejetée."
            issues.append(AuditIssue("ERROR", row.row_id, row.section, msg, current_line=line, expected=f"{row.partition} / {row.total} / attaques fortes porteuses", observed=f"{partition} / {total}"))
            report.append(f"❌ Row {row.row_id:03d} | {row.section}")
            report.append(f"   TEXTE   : {line}")
            report.append(f"   CIBLE   : {row.partition} ({row.total})")
            report.append(f"   OBTENU  : {partition} ({total})")
            for ae in attack_errors:
                report.append(f"   ❌ ATTAQUE FORTE : {ae}")
        if stress and row.stress and stress != row.stress:
            warnings += 1
            report.append(f"   ⚠️ Rythme cible: {row.stress} | obtenu: {stress}")
        for aw in attack_warnings:
            warnings += 1
            report.append(f"   ⚠️ Attaque forte à surveiller : {aw}")
        if rhyme and row.rhyme and row.rhyme != "-" and rhyme != row.rhyme:
            warnings += 1
            report.append(f"   ⚠️ Rime cible: {row.rhyme} | obtenue: {rhyme}")

    report.append("\n3. BILAN")
    report.append(f"Erreurs structurelles/métriques : {len([x for x in issues if x.severity == 'ERROR'])}")
    report.append(f"Erreurs métriques fatales       : {fatal_metric}")
    report.append(f"Erreurs attaques fortes fatales : {fatal_attack}")
    report.append(f"Avertissements rythme/rime/attaque : {warnings}")
    report.append("STATUT FINAL : " + ("✅ CONFORME" if not issues else "❌ CORRECTION REQUISE"))
    return "\n".join(report), issues


def build_correction_prompt(audit_report: str, final_text: str) -> str:
    tpl = load_template(AUDIT_CORRECTION_TEMPLATE)
    return tpl.replace("{{AUDIT_REPORT}}", audit_report.strip()).replace("{{FINAL_TEXT}}", final_text.strip())


def html_escape_text(text: str) -> str:
    return html.escape(text, quote=False)
