# --- MOTEUR PHONÉTIQUE CENTRAL (BASÉ SUR G2P + CORRECTIFS ET ADN RYTHMIQUE) ---
import re
try:
    from g2p_en import G2p
    g2p_model = G2p()
except ImportError:
    print("ATTENTION: g2p_en n'est pas installé. Lancez via le fichier .bat.")
    g2p_model = None
except Exception as e:
    print(f"ERREUR NLTK: Un module est manquant. Lancez SETUP_NLTK.py. Détails: {e}")
    g2p_model = None

# DICTIONNAIRE D'EXCEPTIONS MUSICALES
# Contourne la rigidité du dictionnaire académique pour le chant Pop/Rock/Folk
DICTIONNAIRE_MUSICAL = {
    "ouh": 1, "ah": 1, "oh": 1, "yeah": 1, "hey": 1, "ooh": 1, "mmm": 1, 
    "hm": 1, "mm-hmm": 2, "uh": 1, "woo": 1, "whoa": 1,
    "every": 2, "ev'ry": 2, 
    "memories": 3, "memory": 2, 
    "different": 2, "diff'rent": 2,
    "fire": 1, "desire": 2, 
    "choir": 1, "hour": 1, "our": 1, 
    "power": 2, "flower": 2,
    "rhythm": 2, "heaven": 2, "even": 2, "given": 2
}

def analyser_ADN_phonetique(text):
    """
    Extrait l'ADN complet du segment : Compte syllabique, Rythme (da DUM), Rime ARPAbet.
    """
    if not g2p_model or not text or not text.strip():
        return {"count": 0, "stress_pattern": "", "end_rhyme": ""}
    
    # Normalisation des apostrophes
    text = text.replace("’", "'").replace("‘", "'").replace("´", "'")
    clean_text = re.sub(r"[^a-zA-Z0-9']", " ", text)
    if not clean_text.strip(): 
        return {"count": 0, "stress_pattern": "", "end_rhyme": ""}

    mots = clean_text.split()
    total_syllabes = 0
    stress_list = []
    end_rhyme = ""
    
    for mot in mots:
        mot_lower = mot.lower()
        if mot_lower in DICTIONNAIRE_MUSICAL:
            syll = DICTIONNAIRE_MUSICAL[mot_lower]
            total_syllabes += syll
            if syll > 0:
                stress_list.append("DUM") # 1ère syllabe accentuée par défaut
                stress_list.extend(["da"] * (syll - 1)) # Le reste atone
            end_rhyme = "OOV" # Out Of Vocabulary
        else:
            phonemes = g2p_model(mot)
            for i, p in enumerate(phonemes):
                # Si le phonème se termine par un chiffre, c'est une voyelle (noyau syllabique)
                if p[-1].isdigit():
                    total_syllabes += 1
                    # 1 = Accent principal, 2 = Secondaire -> DUM | 0 = Atone -> da
                    stress_list.append("DUM" if p[-1] in ['1', '2'] else "da")
                    # Capture la dernière voyelle et ses consonnes terminales pour identifier la rime
                    end_rhyme = "-".join(phonemes[i:])
                    
    stress_pattern = " ".join(stress_list)
    return {"count": total_syllabes, "stress_pattern": stress_pattern, "end_rhyme": end_rhyme}

def compter_syllabes_phonetiques(text):
    """
    Fonction de rétrocompatibilité maintenue pour l'auditeur_final.py
    """
    return analyser_ADN_phonetique(text)["count"]