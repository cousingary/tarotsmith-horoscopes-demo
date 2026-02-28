# Editor — System Prompt

This file documents the structure and function of the editor prompt.
The full prompt text is proprietary and not included in this mirror.

---

## Role

Voice guardian and quality enforcer. Does not rewrite. Returns structured
JSON flagging specific failures for the pipeline to act on.

---

## Input

A batch of 4–6 horoscopes (Sun sign or Rising sign) as plain text.

---

## Output Contract

Returns valid JSON only. No preamble.

```json
{
  "overall_quality": "pass" | "revise",
  "batch_notes": "1-2 sentences on the batch overall.",
  "sign_notes": {
    "Aries": ["specific note", ...],
    // all signs in batch must appear as keys
  },
  "differentiation_failures": [
    {
      "signs": ["Sign A", "Sign B"],
      "transit": "transit name",
      "issue": "precise description of the shared failure"
    }
  ],
  "structural_issues": ["missing labels, format violations"]
}
```

`overall_quality` is `"pass"` only when: all mandatory labels present,
no banned words, no differentiation failures, no non-specific mandates,
no element register failures, sign_notes empty or trivial.

---

## What the Editor Checks

**Structural:** mandatory labels present (`Theme:`, `Weekly Mandate:` / `Mandate:`,
date range line).

**Voice:** banned words caught and quoted. Passive constructions flagged.
Planets that "whisper", "suggest", or "offer" rather than act — flagged.
Explanatory hedges ("this may mean", "you might find") — flagged.

**Element register (Sun signs):** fire, earth, air signs written in water-register
language (fluid, currents, fog, dissolution) — flagged as element register failure.

**Differentiation:** two signs receiving the same thematic frame or emotional
register, even in different words — flagged as differentiation failure.

**Mandate quality:** mandate that could close any other sign's horoscope
that week — flagged as non-specific mandate and quoted.
