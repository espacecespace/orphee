# -*- coding: utf-8 -*-
"""
Moteur phonétique compatible ORPHÉE v8
======================================
Expose : analyser_ADN_phonetique(text) -> {count, stress_pattern, end_rhyme}

Priorité :
1. CMUDict via NLTK pour les mots connus.
2. g2p_en en fallback pour les mots inconnus, si disponible.
3. Heuristique syllabique si aucune ressource n'est disponible.

Ce fichier est autonome pour Streamlit Cloud : si les ressources NLTK ne sont pas
encore installées, il tente de les télécharger silencieusement. Parce qu'échouer
sur un dictionnaire absent au milieu d'un refrain, c'est une forme d'art ratée.
"""
from __future__ import annotations

import re
from functools import lru_cache

_WORD_RE = re.compile(r"[A-Za-zÀ-ÿ']+")
_CMU = None
_G2P = None


def _load_cmu():
    global _CMU
    if _CMU is not None:
        return _CMU
    try:
        import nltk
        try:
            from nltk.corpus import cmudict
            _CMU = cmudict.dict()
        except LookupError:
            nltk.download("cmudict", quiet=True)
            from nltk.corpus import cmudict
            _CMU = cmudict.dict()
    except Exception:
        _CMU = {}
    return _CMU


def _load_g2p():
    global _G2P
    if _G2P is not None:
        return _G2P
    try:
        import nltk
        for corpus in ["averaged_perceptron_tagger", "averaged_perceptron_tagger_eng"]:
            try:
                nltk.download(corpus, quiet=True)
            except Exception:
                pass
        from g2p_en import G2p
        _G2P = G2p()
    except Exception:
        _G2P = False
    return _G2P


def _normalize_word(word: str) -> str:
    return re.sub(r"[^a-z']", "", word.lower())


def _heuristic_syllables(word: str) -> int:
    w = _normalize_word(word)
    if not w:
        return 0
    contractions = {
        "i'm": 1, "you're": 1, "we're": 1, "they're": 1, "it's": 1,
        "don't": 1, "can't": 1, "won't": 1, "isn't": 2, "wasn't": 2,
        "would've": 2, "could've": 2, "should've": 2, "gonna": 2,
        "wanna": 2, "gotta": 2,
    }
    if w in contractions:
        return contractions[w]
    groups = re.findall(r"[aeiouy]+", w)
    count = len(groups)
    if w.endswith("e") and not w.endswith(("le", "ye")) and count > 1:
        count -= 1
    if w.endswith("ed") and count > 1 and not re.search(r"(ted|ded)$", w):
        count -= 1
    return max(1, count)


def _pron_syllables(pron: list[str]) -> int:
    return sum(1 for p in pron if any(ch.isdigit() for ch in p))


def _stress_for_pron(pron: list[str]) -> str:
    out = []
    for p in pron:
        if any(ch.isdigit() for ch in p):
            out.append("DUM" if "1" in p or "2" in p else "da")
    return " ".join(out)


def _end_rhyme_for_pron(pron: list[str]) -> str:
    vowels = [(i, p) for i, p in enumerate(pron) if any(ch.isdigit() for ch in p)]
    if not vowels:
        return "-"
    chosen_idx, chosen = None, None
    for i, p in reversed(vowels):
        if "1" in p:
            chosen_idx, chosen = i, p
            break
    if chosen is None:
        chosen_idx, chosen = vowels[-1]
    tail = pron[chosen_idx:]
    cleaned = [re.sub(r"[^A-Z0-9]", "", x) for x in tail]
    return "-".join(cleaned) if cleaned else "-"


def _g2p_pron(word: str) -> list[str] | None:
    g2p = _load_g2p()
    if not g2p:
        return None
    try:
        phones = g2p(word)
        pron = [p for p in phones if isinstance(p, str) and p.strip() and p != " "]
        if any(any(ch.isdigit() for ch in p) for p in pron):
            return pron
    except Exception:
        return None
    return None


@lru_cache(maxsize=30000)
def _analyze_word(word: str) -> tuple[int, str, str]:
    w = _normalize_word(word)
    if not w:
        return 0, "", "-"

    cmu = _load_cmu()
    if w in cmu:
        pron = cmu[w][0]
        return _pron_syllables(pron), _stress_for_pron(pron), _end_rhyme_for_pron(pron)

    pron = _g2p_pron(w)
    if pron:
        return _pron_syllables(pron), _stress_for_pron(pron), _end_rhyme_for_pron(pron)

    cnt = _heuristic_syllables(w)
    return cnt, " ".join(["DUM"] * cnt), "-"


def analyser_ADN_phonetique(text: str) -> dict:
    words = _WORD_RE.findall(text or "")
    total = 0
    stresses = []
    end_rhyme = "-"
    for word in words:
        cnt, stress, rhyme = _analyze_word(word)
        total += cnt
        if stress:
            stresses.append(stress)
        if rhyme and rhyme != "-":
            end_rhyme = rhyme
    return {
        "count": total,
        "stress_pattern": " ".join(stresses),
        "end_rhyme": end_rhyme,
    }
