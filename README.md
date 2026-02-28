# Tarotsmith Horoscope Engine — Public Mirror

Production system for generating weekly Sun and Rising sign horoscopes from real ephemeris data.

Live output: [horoscopes.tarotsmith.com](https://horoscopes.tarotsmith.com)

---

## What This Is

A fully automated weekly pipeline that transforms structured planetary data into 24 differentiated horoscope texts — 12 Sun sign, 12 Rising sign — and publishes them to WordPress without human intervention beyond the initial data entry.

This repository is a public mirror of a private production system. It documents architecture, data modelling, orchestration design, and publication workflow. Proprietary prompt frameworks and internal QA logic are not included.

The goal is not content generation at scale. It is consistent, high-fidelity symbolic synthesis with strict voice control — output that reads as written, not generated.

---

## System Architecture

### Data Layer

Weekly planetary data is entered into a structured CSV before the Monday generation run. No external API dependency at generation time. The pipeline reads from local ephemeris data only.

```
week_start, week_end,
Sun_transit, Moon_transit, Mercury_transit, Venus_transit,
Mars_transit, Jupiter_transit, Saturn_transit,
Uranus_transit, Neptune_transit, Pluto_transit,
Node_transit, Lilith_transit, Chiron_transit
```

From this, `generate.py` derives:

- Sign relationships (trine, square, opposition, conjunction, etc.)
- Solar dignity (domicile, exaltation, detriment, fall, peregrine)
- Retrograde flags
- Lunar phase and Sun–Moon separation
- Whole-sign house placements for all 12 Rising sign variants
- Aspect stack ranked by orb, filtered by planet weight

### Generation Pipeline

```
CSV → parse positions → derive aspects → build 24 sign briefs
    → Sun writer (batches of 4) → editor pass → conditional revision
    → Rising writer (batches of 4) → editor pass → conditional revision
    → assemble output JSON → commit to repo
```

The writer and editor are distinct roles with separate system prompts. The editor does not rewrite — it returns structured JSON flagging specific failures. The pipeline acts on those flags with a single revision pass per batch.

Currently runs on ChatGPT (GPT-4.1). The pipeline is model-agnostic: any provider can be substituted via environment variable.

### Publication Pipeline

```
output/YYYY-MM-DD.json → post_to_wordpress.py → 24 WordPress pages updated
                       → update_index.py → index page date and chart image updated
```

Both steps run automatically on Sunday afternoon Bangkok time via GitHub Actions, before the Monday readership arrives.

---

## Repository Structure

```
/src
  chart_parser.py        # parses CSV positions into structured dicts
  transit_engine.py      # aspect calculation, dignity, lunar phase, house placement
  pipeline.py            # orchestrator: brief builder, writer calls, editor loop

/prompts
  system_sun.md          # Sun sign writer prompt (structure documented, content excluded)
  system_rising.md       # Rising sign writer prompt (structure documented, content excluded)
  editor.md              # Editor prompt (structure documented, content excluded)

/data
  weekly_snapshot_example.csv   # anonymised example of the ephemeris input format

/examples
  sample_output.md       # real generated output, week of 2 March–8 March 2026

/.github/workflows
  generate_horoscopes.yml   # Monday 11:11 AM Bangkok: runs pipeline, commits JSON
  publish_horoscopes.yml    # Sunday 15:33 Bangkok: posts to WordPress
  weekly_update.yml         # Sunday 15:40 Bangkok: updates index page
```

---

## What the Prompt Stack Does (Without Showing It)

Each role in the pipeline operates under explicit constraints enforced at the prompt level:

**Sun sign writer** receives a structured JSON brief for each sign containing exact planetary degrees, aspect list ranked by orb, solar dignity, retrograde flags, lunar phase, and a tarot decan card derived from the Sun's exact degree. It is constrained to write the sign's native agenda interrupted by the week's sky — not the sky's character described generically. A banned phrase list prevents register drift. Element register is enforced: fire signs experience a Pisces stellium as disruption to ignition, not as immersion in water.

**Rising sign writer** receives whole-sign house placements for each of the 12 ascendant variants. It is constrained to write specific events in specific houses — not emotional registers, but things that happen in rooms. Each mandate must name a specific act in a specific domain; a mandate that could close any other Rising sign's horoscope that week is a failure condition.

**Editor** returns structured JSON. It does not prose-edit. It flags: banned words, differentiation failures (two signs receiving the same story in different words), element register violations, non-specific mandates, passive constructions that drain authority. The pipeline reads the JSON and retries flagged signs once. The editor report is committed to the repo alongside the output for review.

---

## Failure Modes Managed

**Voice drift across signs.** When three or more planets occupy one sign, the failure mode is writing twelve variants of that sign's experience. The prompt architecture explicitly addresses this by requiring the writer to name the previous sign's story before writing the current one, and confirm the stories are structurally different.

**Late-batch quality collapse.** Writing 12 signs sequentially degrades. The pipeline batches in groups of 4 (or 6) with a fresh editor pass after each batch.

**Generic mandate problem.** Horoscopes routinely end in language that could close any week for any sign. The editor flags this explicitly. The mandate is required to name an act and a domain — "finalise the contract" not "trust the process."

**Element register contamination.** Water-register language (fluid, dissolving, drifting) applied to fire, earth, and air signs is a distinct failure mode, especially under a Pisces stellium. The editor checks for this per sign.

---

## Automation

Three GitHub Actions workflows handle the full cycle:

| Workflow | Trigger | Function |
|---|---|---|
| `generate_horoscopes.yml` | Monday 04:00 UTC | Runs pipeline, commits JSON output |
| `publish_horoscopes.yml` | Sunday 08:33 UTC | Posts 24 horoscope pages to WordPress |
| `weekly_update.yml` | Sunday 08:40 UTC | Updates index page date and chart image |

The 7-minute gap between the two Sunday workflows ensures sign pages are live before the index links to them. All credentials are GitHub Secrets. Model and temperature are GitHub Variables with defaults, overridable without code changes.

---

## Example Output

**→ [examples/sample_output.md](examples/sample_output.md)**

Real output from the week of 2 March–8 March 2026 against the actual sky. Three Sun sign and three Rising sign examples. These are not sanitised — they reflect the pipeline's actual editorial standard, including the structural choices the prompt stack enforces.

---

## Tech Stack

- **Python 3.12**
- **OpenAI API** (currently GPT-4.1 for writer, GPT-4.1 for editor — configurable via GitHub secrets)
- **WordPress REST API** (Application Password auth)
- **GitHub Actions** (scheduling, secrets management, output archiving)

The pipeline is model-agnostic. `OPENAI_MODEL` and `EDITOR_MODEL` are environment variables. Any OpenAI-compatible endpoint can be substituted.

---

## Status

Active production system. Weekly output published live since February 2026.

Built and maintained by [Jeremy Lamkin](https://github.com/cousingary).
