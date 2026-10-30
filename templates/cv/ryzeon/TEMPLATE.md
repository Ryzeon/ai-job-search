# Template: ryzeon

- **Type:** CV
- **Source extension:** `.json`
- **Compile command:** `python3 ../tools/ryzeon_cv.py build main_<company>_<role>.json`
- **Engine/toolchain:** cv.ryzeon.dev API + headless Chrome (print to PDF)
- **Page limit:** 2 page(s)
- **Fonts:** defined by the web template chosen in `"template"`; nothing to install

## What it is

The CV is not typeset locally. The source file is the JSON payload of the
[ryz-cv-web](https://github.com/Ryzeon/ryz-cv-web) API (contract: `GET /api/cv/schema/`).
Compiling publishes it at a private link (`https://cv.ryzeon.dev/cv/<id>/`) that the
recruiter can open, and prints that page to `main_<company>_<role>.pdf` for portals that
want an attachment. Re-compiling updates the same link (the id is kept in `<file>.id`).

Contact details (email, phone, links, address) are **inherited from the site profile** —
never put them in the payload.

## Style rules

- `"template"`: `compact` is the default and the one that fits two pages most easily
  (~70 bullets). `ats-plain` for Workday/Taleo/Greenhouse-style portals (~45-50 bullets).
  `harvard`, `modern`, `timeline` (~48) and `canada` (Letter, ~46) also exist.
- `"lang"`: the language the posting is written in (`en` or `es`). One language per CV.
- Section order: Summary → Experience → Selected Projects → Skills → Education →
  Languages → Certifications. Move a project above Experience only when the posting is
  about something proven there rather than at work.
- Bullets say what problem was solved and what changed, with the technology at the end.
  No class names, annotation names or file counts. Percentages over raw counts.
- In Spanish, write Peruvian Spanish (no "vosotros", "ordenador", "móvil").
- Never stress that the candidate holds several jobs at once.

## Known pitfalls

- `verify_layout.py` thresholds are calibrated for moderncv; the web templates have their
  own margins, so treat a "phantom hole" report with suspicion and look at the PDF.
- The PDF must come from `build`, not from a browser print dialog: the page-count badge on
  the site is an estimate, the printed PDF is the truth.
- A `422` from the API lists the schema `issues[]`; fix the JSON and rebuild.
- `401`: the token is missing or stale (`vercel env pull --yes` in ryz-cv-web).
