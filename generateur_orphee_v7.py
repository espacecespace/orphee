# ==============================================================================
# ORPHÉE-ULTRA v7 — FONCTIONS DE TRAITEMENT (VERSION WEB — BI-PROMPT)
#
# Architecture : 2 prompts / 2 conversations distinctes
#   PROMPT 1 (ORPHÉE-CRÉATIF)   → Tableau RÉDUIT  (# | Section | Total)
#   PROMPT 2 (ORPHÉE-ÉDITORIAL) → Tableau COMPLET + zone Handoff Package
#
# Fonctions exportées :
#   detecter_langue()               → routeur FR / EN
#   est_balise_section()            → détecte [VERSE], [CHORUS], etc.
#   analyser_paroles_vers_tableau() → génère le tableau Markdown acoustique COMPLET
#   generer_tableau_reduit()        → filtre le tableau complet → colonnes # | Section | Total
#   nettoyer_titre()                → formate le nom de fichier en titre
#   injecter_tableau()              → injecte dans la zone °#x#°0° ... °#x#°9°
#   injecter_handoff()              → injecte le Handoff Package dans °#h#°0° ... °#h#°9°
#   assembler_prompt_1()            → assemble le Prompt 1 complet
#   assembler_prompt_2()            → assemble le Prompt 2 complet
# ==============================================================================

import re
import os

try:
    from moteur_phonetique import analyser_ADN_phonetique
    MOTEUR_ACTIF = True
except ImportError:
    MOTEUR_ACTIF = False
    def analyser_ADN_phonetique(text):
        return {"count": 0, "stress_pattern": "", "end_rhyme": "-"}


# ==============================================================================
# DÉTECTEUR DE LANGUE
# ==============================================================================

def detecter_langue(texte_paroles):
    """Routeur bilingue FRANÇAIS / ENGLISH."""
    mots_fr = r"\b(le|la|les|un|une|des|et|ou|dans|je|tu|il|nous|vous|c'est|mon|ma|sur|pour|avec|mais)\b"
    mots_en = r"\b(the|a|an|is|are|was|were|have|has|with|from|they|you|he|she|we|and|but|if|to|of|in|on)\b"
    score_fr = len(re.findall(mots_fr, texte_paroles, re.IGNORECASE))
    score_en = len(re.findall(mots_en, texte_paroles, re.IGNORECASE))
    if score_fr > score_en * 1.2:
        return "FRANÇAIS"
    return "ENGLISH"


# ==============================================================================
# DÉTECTION DES BALISES DE SECTION
# ==============================================================================

def est_balise_section(ligne):
    """Détecte les balises de structure musicale ([VERSE], [CHORUS], [COUPLET], etc.)."""
    s = ligne.strip()
    if s.startswith('[') and s.endswith(']'):
        interieur = s[1:-1].strip()
        if len(interieur) <= 40 and re.match(r'^[A-Za-zÀ-ÿ0-9\s\-]+$', interieur):
            return True, s.upper()
    return False, None


# ==============================================================================
# ANALYSEUR PHONÉTIQUE — TABLEAU ACOUSTIQUE COMPLET
# ==============================================================================

def analyser_paroles_vers_tableau(lignes_paroles):
    """
    Génère le tableau Markdown d'ADN acoustique COMPLET.
    Colonnes : # | Section | PARTITION | Total | Rythme (Stress) | Rime Fin | Texte Source
    Destiné à Prompt 2 (ORPHÉE-ÉDITORIAL).
    """
    tableau_md = [
        "| # | Section | PARTITION | Total | Rythme (Stress) | Rime Fin | Texte Source |",
        "|---|---|---|:---:|---|---|---|"
    ]

    line_id = 1
    section_counters = {}
    current_section_display = "[INTRO] #1"

    for ligne in lignes_paroles:
        raw = ligne.rstrip('\n')
        clean = raw.strip().replace("|", "/")

        if not clean:
            continue

        is_balise, tag = est_balise_section(clean)
        if is_balise:
            count = section_counters.get(tag, 0) + 1
            section_counters[tag] = count
            current_section_display = f"{tag} #{count}"
            continue

        clean_calc = re.sub(r"\(.*?\)", "", clean).strip()
        if not clean_calc:
            clean_calc = clean

        segments = re.split(r'([,;\-\.!\?])', clean_calc)
        partitions    = []
        ligne_stresses = []
        total_syll    = 0
        derniere_rime = ""
        buffer        = ""

        for seg in segments:
            if seg in [',', ';', '-', '.', '!', '?']:
                if buffer.strip():
                    adn = analyser_ADN_phonetique(buffer)
                    partitions.append(f"[{adn['count']}]")
                    total_syll += adn['count']
                    if adn['stress_pattern']:
                        ligne_stresses.append(adn['stress_pattern'])
                    if adn['end_rhyme']:
                        derniere_rime = adn['end_rhyme']
                    buffer = ""
            else:
                buffer += seg

        if buffer.strip():
            adn = analyser_ADN_phonetique(buffer)
            partitions.append(f"[{adn['count']}]")
            total_syll += adn['count']
            if adn['stress_pattern']:
                ligne_stresses.append(adn['stress_pattern'])
            if adn['end_rhyme']:
                derniere_rime = adn['end_rhyme']

        partition_str  = ' + '.join(partitions) if partitions else "[0]"
        rythme_str     = ' / '.join(ligne_stresses) if ligne_stresses else ""
        if not derniere_rime:
            derniere_rime = "-"

        tableau_md.append(
            f"| {line_id} | {current_section_display} | {partition_str} | {total_syll} | "
            f"{rythme_str} | {derniere_rime} | {clean} |"
        )
        line_id += 1

    return "\n".join(tableau_md)


# ==============================================================================
# TABLEAU RÉDUIT — PROMPT 1 UNIQUEMENT
# ==============================================================================

def generer_tableau_reduit(tableau_complet):
    """
    Filtre le tableau complet pour ne garder que les colonnes
    # | Section | Total (cibles syllabiques).
    Supprime PARTITION, Rythme, Rime Fin, Texte Source.
    Destiné à Prompt 1 (ORPHÉE-CRÉATIF).
    """
    lignes = tableau_complet.split('\n')
    lignes_reduites = []

    for ligne in lignes:
        if not ligne.startswith('|'):
            continue
        colonnes = [c.strip() for c in ligne.split('|')]
        if len(colonnes) >= 5:
            col_num     = colonnes[1]
            col_section = colonnes[2]
            col_total   = colonnes[4]
            if col_num == '#':
                lignes_reduites.append("| # | Section | Total |")
            elif col_num == '---':
                lignes_reduites.append("|---|---|:---:|")
            else:
                lignes_reduites.append(f"| {col_num} | {col_section} | {col_total} |")

    return '\n'.join(lignes_reduites)


# ==============================================================================
# NETTOYAGE DU TITRE
# ==============================================================================

def nettoyer_titre(nom_fichier_sans_ext):
    """Transforme un nom de fichier (sans extension) en titre lisible en majuscules."""
    return nom_fichier_sans_ext.replace("_", " ").replace("-", " ").upper()


# ==============================================================================
# INJECTION DU TABLEAU ACOUSTIQUE  °#x#°0° … °#x#°9°
# ==============================================================================

PATTERN_ZONE_TABLEAU = re.compile(r"°#x#°0°.*?°#x#°9°", re.DOTALL)

def injecter_tableau(gabarit, tableau_analyse):
    """Injecte un tableau acoustique dans la zone °#x#°0° … °#x#°9°."""
    remplacement = f"°#x#°0°\n{tableau_analyse}\n°#x#°9°"
    if PATTERN_ZONE_TABLEAU.search(gabarit):
        return PATTERN_ZONE_TABLEAU.sub(remplacement, gabarit)
    else:
        return gabarit + f"\n\n<!-- ACOUSTIC BLUEPRINT — INJECTION FALLBACK -->\n{remplacement}"


# ==============================================================================
# INJECTION DU HANDOFF PACKAGE  °#h#°0° … °#h#°9°
# ==============================================================================

PATTERN_ZONE_HANDOFF = re.compile(r"°#h#°0°.*?°#h#°9°", re.DOTALL)

def injecter_handoff(gabarit_2, handoff_package):
    """
    Injecte le Handoff Package (produit par le Prompt 1) dans la zone
    °#h#°0° … °#h#°9° du gabarit Éditorial.
    """
    remplacement = f"°#h#°0°\n{handoff_package.strip()}\n°#h#°9°"
    if PATTERN_ZONE_HANDOFF.search(gabarit_2):
        return PATTERN_ZONE_HANDOFF.sub(remplacement, gabarit_2)
    else:
        return f"°#h#°0°\n{handoff_package.strip()}\n°#h#°9°\n\n" + gabarit_2


# ==============================================================================
# ASSEMBLAGE — PROMPT 1 (ORPHÉE-CRÉATIF)
# ==============================================================================

def assembler_prompt_1(gabarit_1, titre, yaourt):
    """
    Assemble le Prompt 1 (Phase Créative) :
      - Remplace [TITRE_DE_LA_CHANSON_AUTOMATIQUE] et [LANGUE_DÉTÉCTÉE]
      - Injecte le tableau RÉDUIT (# | Section | Total)
    Retourne (prompt_1_str, langue_str, nb_lignes_int).
    """
    lignes = yaourt.splitlines(keepends=True)
    texte_plat = " ".join(
        l.strip() for l in lignes
        if l.strip() and not est_balise_section(l.strip())[0]
    )
    langue = detecter_langue(texte_plat)

    tableau_complet = analyser_paroles_vers_tableau(lignes)
    tableau_reduit  = generer_tableau_reduit(tableau_complet)
    nb_lignes = tableau_complet.count('\n') - 1

    prompt = gabarit_1
    prompt = prompt.replace("[TITRE_DE_LA_CHANSON_AUTOMATIQUE]", titre.upper().strip())
    prompt = prompt.replace("[LANGUE_DÉTÉCTÉE]", langue)
    prompt = injecter_tableau(prompt, tableau_reduit)

    return prompt, langue, nb_lignes


# ==============================================================================
# ASSEMBLAGE — PROMPT 2 (ORPHÉE-ÉDITORIAL)
# ==============================================================================

def assembler_prompt_2(gabarit_2, titre, yaourt, handoff_package):
    """
    Assemble le Prompt 2 (Phase Éditoriale) :
      - Remplace [TITRE_DE_LA_CHANSON_AUTOMATIQUE] et [LANGUE_DÉTÉCTÉE]
      - Injecte le tableau COMPLET (toutes colonnes)
      - Injecte le Handoff Package dans la zone °#h#°0° … °#h#°9°
    Retourne (prompt_2_str, langue_str).
    """
    lignes = yaourt.splitlines(keepends=True)
    texte_plat = " ".join(
        l.strip() for l in lignes
        if l.strip() and not est_balise_section(l.strip())[0]
    )
    langue = detecter_langue(texte_plat)

    tableau_complet = analyser_paroles_vers_tableau(lignes)

    prompt = gabarit_2
    prompt = prompt.replace("[TITRE_DE_LA_CHANSON_AUTOMATIQUE]", titre.upper().strip())
    prompt = prompt.replace("[LANGUE_DÉTÉCTÉE]", langue)
    prompt = injecter_tableau(prompt, tableau_complet)
    prompt = injecter_handoff(prompt, handoff_package)

    return prompt, langue
