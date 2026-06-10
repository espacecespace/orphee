# ==============================================================================
# ORPHÉE-ULTRA v5 — FONCTIONS DE TRAITEMENT (VERSION WEB)
#
# Ce fichier est une version allégée de generateur_orphee_v5.py original.
# Le pipeline CLI (lecture/écriture de dossiers, archivage) a été retiré.
# Toutes les fonctions de traitement sont IDENTIQUES à l'original.
#
# Fonctions exportées :
#   detecter_langue()              → routeur FR / EN
#   est_balise_section()           → détecte [VERSE], [CHORUS], etc.
#   analyser_paroles_vers_tableau() → génère le tableau Markdown acoustique
#   nettoyer_titre()               → formate le nom de fichier en titre
#   injecter_tableau()             → injecte le tableau dans le gabarit
# ==============================================================================

import re

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
# ANALYSEUR PHONÉTIQUE — GÉNÉRATION DU TABLEAU ACOUSTIQUE (identique à l'original)
# ==============================================================================

def analyser_paroles_vers_tableau(lignes_paroles):
    """
    Génère le tableau Markdown d'ADN acoustique (code-barres syllabique)
    à partir des lignes de yaourt. Injecté dans la zone acoustique du gabarit.
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
# NETTOYAGE DU TITRE
# ==============================================================================

def nettoyer_titre(nom_fichier_sans_ext):
    """Transforme le nom de fichier en titre lisible."""
    return nom_fichier_sans_ext.replace("_", " ").replace("-", " ").upper()


# ==============================================================================
# INJECTION DU TABLEAU ACOUSTIQUE DANS LE GABARIT
# ==============================================================================

PATTERN_ZONE_TABLEAU = re.compile(r"°#x#°0°.*?°#x#°9°", re.DOTALL)

def injecter_tableau(gabarit, tableau_analyse):
    """Injecte le tableau acoustique dans la zone prévue du Bloc 2 (Acoustic Blueprint)."""
    remplacement = f"°#x#°0°\n{tableau_analyse}\n°#x#°9°"
    if PATTERN_ZONE_TABLEAU.search(gabarit):
        return PATTERN_ZONE_TABLEAU.sub(remplacement, gabarit)
    else:
        print("⚠️  Zone acoustique introuvable dans le gabarit — tableau ajouté en fin de fichier.")
        return gabarit + f"\n\n<!-- ACOUSTIC BLUEPRINT — INJECTION FALLBACK -->\n{remplacement}"
