---
name: getonbrd-search
version: 1.0.0
description: >
  Search Get on Board (getonbrd.com), the main tech job board for Latin America, for
  remote postings and check each one's real remote policy (open worldwide vs. only for
  residents of named countries). Use when the user wants remote tech jobs in LATAM,
  Peru, Chile, Colombia, Mexico, Argentina, or "Get on Board"/"getonbrd" jobs.
context: fork
enabled: true
---

# Get on Board Search Skill

Public API + public job pages, standard-library Python, no auth.

## Commands

```bash
# Remote postings from the last 14 days, open to Peru or to anywhere
python3 .agents/skills/getonbrd-search/cli.py search -q java -q "spring boot" -q "ai engineer" -q "full stack" --days 14 --country Peru

# One posting: requirements, functions, nice-to-haves, remote policy, application language
python3 .agents/skills/getonbrd-search/cli.py detail <job-id>
```

`search` prints JSON with `remote_policy`, `apply_language` and `eligible` per job.

## Rules that matter

- The API's `remote: true` is **not** enough: many postings are "Locally remote only"
  (100% remote but only for residents of one country). Always check `remote_policy`.
- `apply_language: English` means the application form must be written in English.
- Keep volume low (a handful of queries per run); the job pages are fetched one by one.
- Applying happens on the site (logged-in session in the browser), not through this CLI.
