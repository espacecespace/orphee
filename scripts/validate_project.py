from __future__ import annotations

import py_compile
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "app.py",
    "orphee_core.py",
    "moteur_phonetique.py",
    "auditeur_final_cli.py",
    "requirements.txt",
    "ORPHEE_SOURCE_PROMPT_1_v1_2_FINAL.txt",
    "ORPHEE_TOPLINER_PROMPT_2_v1_0_FINAL.txt",
    "ORPHEE_FINALIZER_PROMPT_3_v1_0_FINAL.txt",
    "ORPHEE_AUDIT_CORRECTION_v1_0.txt",
)
PYTHON_FILES = (
    "app.py",
    "orphee_core.py",
    "moteur_phonetique.py",
    "auditeur_final_cli.py",
)


def main() -> int:
    missing = [name for name in REQUIRED_FILES if not (ROOT / name).is_file()]
    if missing:
        print("Fichiers requis absents : " + ", ".join(missing), file=sys.stderr)
        return 1

    for name in PYTHON_FILES:
        py_compile.compile(str(ROOT / name), doraise=True)

    print(f"Validation structure + syntaxe OK ({len(REQUIRED_FILES)} fichiers requis).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
