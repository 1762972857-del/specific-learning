# Contributing

This guide is for people changing the repository. The agent-facing instructions are in `SKILL.md` and `references/`; keep them about building a lab, not about maintaining the repo.

## Repository roles

- `templates/<name>/` are starting points that `scripts/new_topic.py` copies. Each has a runnable `model.py`, a page and a notes skeleton, with `TOPIC:` placeholders where prose belongs.
- `examples/<name>/` are finished reference deliverables. They are never copied by the scaffold.
- `assets/`, `scripts/build.py`, `scripts/check.py`, `scripts/bundle_notes.py` and `scripts/qa.py` are the shared copies. In each example, `viz/assets`, `viz/build.py`, `viz/check.py`, `viz/bundle_notes.py` and `viz/qa.py` are relative symlinks to them. The scaffold copies real files so generated topics work standalone.

Examples and templates are different roles on purpose. Do not merge them or treat one as a duplicate of the other.

## Adding a template

1. Create `templates/<name>/` with `viz/<name>.html`, `viz/model.py` (`evaluate`, `DEFAULTS`, `DEFAULT_INPUTS`, `CHECK_CASES`, optional `extra_checks(report)`) and `notes/01-<name>.md`, plus `viz/qa.json` with one or two real interactions (run `python3 viz/qa.py` on a scaffold). Page, model and notes use `TOPIC:` placeholders instead of finished prose.
2. Nothing needs registering: `new_topic.py` lists every directory that contains `viz/<name>.html`.
3. Add a row to the "Course routes" table in `references/interpretation.md`, naming the subject area, the drawing pieces worth reusing and what to watch for.
4. Run `sh scripts/selftest.sh`.

## When to run what

The [CI workflow](.github/workflows/ci.yml) runs the same self-test on pushes to `main`, pull requests, and manual dispatch. It uses Ubuntu, Python 3.12, Node.js 24, and Playwright with Chromium installed. Browser checks may report SKIP locally when unavailable; CI treats that skip as a failure. Automated checks do not replace the visual review in [acceptance.md](references/acceptance.md).

- `sh scripts/selftest.sh` after any change to `assets/`, `scripts/`, `templates/` or `examples/`. It scaffolds every template, checks both examples, runs the surface renderer test and confirms each example bundle is fresh. The browser step (`qa.py`) prints SKIP when Playwright or Chromium is unavailable. It needs `python3` and `node` and must end with `selftest: all passed`.
- `node scripts/verify_surface3d.cjs` after changing `assets/surface3d.js` (selftest also runs it).
- `python3 viz/build.py` from an example directory after editing its notes, figures or model (`--no-figures` keeps the committed figures byte-identical; matplotlib PNGs can differ on regeneration).

## Design principles

- The focus is learning visualization, not a front-end framework. Do not add a component library and do not split examples into components.
- Templates are organized by drawing archetype (curves, fields, superposition, geometry, time evolution and so on). The Course routes table maps subjects to archetypes, so a new subject usually reuses a template rather than adding one.
- Finished labs stay offline and load only the shared assets. Do not add CDN resources or new front-end dependencies.
- `check.py` stays standard-library only. Python packages such as NumPy and matplotlib are optional and only for a topic's own model or figures.
- Verification is case-based. Keep reference values independent of the code under test.

## Style

- Write in English, plainly and concisely.
- A change to a shared asset must keep every template and example passing the checks.
- Vendored KaTeX and marked keep their own licenses. Check the license before adding third-party text, figures or code.
