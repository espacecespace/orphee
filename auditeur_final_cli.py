# -*- coding: utf-8 -*-
"""Auditeur final CLI optionnel pour ORPHÉE LOCAL v9.0."""
from __future__ import annotations
import argparse
from pathlib import Path
from orphee_core import parse_blueprint_table, audit_final_text, build_correction_prompt, ORPHEE_VERSION, CORE_FILE_PATH


def main() -> int:
    ap = argparse.ArgumentParser(description="Auditer un texte final ORPHÉE contre un blueprint complet.")
    ap.add_argument("--blueprint", required=True, help="Fichier contenant le tableau Full Acoustic Blueprint")
    ap.add_argument("--final", required=True, help="Fichier texte final pur avec sections")
    ap.add_argument("--out", default="", help="Fichier rapport à écrire")
    args = ap.parse_args()

    print(f"Moteur actif : {ORPHEE_VERSION} | {CORE_FILE_PATH}")
    blueprint = Path(args.blueprint).read_text(encoding="utf-8")
    final = Path(args.final).read_text(encoding="utf-8")
    rows = parse_blueprint_table(blueprint)
    report, issues = audit_final_text(final, rows)
    correction = build_correction_prompt(report, final)

    if args.out:
        out = Path(args.out)
        out.write_text(report + "\n\n" + "="*80 + "\nPROMPT CORRECTION\n" + "="*80 + "\n" + correction, encoding="utf-8")
        print(f"Rapport écrit : {out}")
    else:
        print(report)
        print("\n" + "="*80 + "\nPROMPT CORRECTION\n" + "="*80 + "\n")
        print(correction)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
