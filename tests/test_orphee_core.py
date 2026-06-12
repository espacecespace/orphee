from __future__ import annotations

from orphee_core import (
    assembler_prompt_1,
    build_context,
    detect_language,
    extract_final_pure_lyrics,
    normalize_run_salt,
    parse_blueprint_table,
    parse_pure_lyrics,
    slugify_filename,
)


def test_slugify_filename_normalizes_french_accents() -> None:
    assert slugify_filename("Été à Montréal") == "ete_a_montreal"


def test_detect_language_distinguishes_common_french_and_english() -> None:
    assert detect_language("je suis dans la nuit et je marche avec toi") == "FRANÇAIS"
    assert detect_language("I am in the night and I walk with you") == "ENGLISH"


def test_free_structure_context_and_prompt_generation() -> None:
    context = build_context(
        title="Northern Lights",
        title_source="test",
        instructions="Write in English with a restrained tone.",
        yaourt="",
        run_salt="run 42",
        creative_mode="Explore New Direction",
    )

    assert context.source_mode == "FREE_STRUCTURE"
    assert context.rows == []
    assert context.creative_run_salt == normalize_run_salt("run 42")

    prompt = assembler_prompt_1(context)
    assert "NORTHERN LIGHTS" in prompt
    assert "FREE_STRUCTURE" in prompt
    assert "LOCAL INTERFACE METADATA" in prompt


def test_parse_blueprint_table_ignores_headers_and_invalid_rows() -> None:
    table = """
| # | Section | Partition | Total | Stress | Rhyme | Source |
|---|---|---|---|---|---|---|
| 1 | [VERSE] | [4] | 4 | DUM da | AY1 | hello world |
| invalid | [VERSE] | [2] | nope | - | - | ignored |
"""

    rows = parse_blueprint_table(table)
    assert len(rows) == 1
    assert rows[0].row_id == 1
    assert rows[0].section == "[VERSE]"
    assert rows[0].total == 4


def test_extract_final_pure_lyrics_from_full_model_output() -> None:
    output = """
Introductory explanation.
FINAL HANDOFF — PURE LYRICS ONLY
```text
[VERSE]
First line
Second line
[CHORUS]
Sing it now
```
CHANGELOG
Nothing below belongs to the lyrics.
"""

    pure = extract_final_pure_lyrics(output)
    tags, lyrics, parasites = parse_pure_lyrics(pure)

    assert tags == ["[VERSE]", "[CHORUS]"]
    assert lyrics == ["First line", "Second line", "Sing it now"]
    assert parasites == []
