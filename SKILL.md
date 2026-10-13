---
name: specific-learning
description: Create interactive labs, original figures, and Markdown learning notes for undergraduate math methods and physics concepts from natural-language questions or uploaded course material. Use for concept learning, interactive notes, or specific learning. Engineering system design, PFD/P&ID, and SDS are out of scope.
---

# Specific Learning

Turn a concept into learning material the reader can explore and check. Deliver by default an interactive HTML lab, Markdown notes with figure-reading guidance, and the static figures the notes need; deliver a subset when asked. Match depth to the user's course and prerequisites.

```text
<topic>/
  sources/                    Uploaded originals, page references
  notes/01-<slug>.md           Learning notes
  viz/
    <slug>.html               Interactive lab
    model.py                  Reference model for figures and verification
    figures.py -> figures/    Optional figures and figures.json
    build.py  check.py  bundle_notes.py  qa.py   Build, verification, offline bundling, browser QA
    assets/                   draft.css/js, optional surface3d.js, local KaTeX and marked
```

## Workflow

Resolve paths from **the directory containing the SKILL.md read for this task**; enter it before scaffolding and do not mix installed and workspace copies. Replace placeholder paths and names with the actual topic.

0. **Check the environment.** Pick the interpreter `PY`, never installing system packages:
   1. `python3`, if `python3 -c "import sys; print(sys.version)"` succeeds within 10 s. On macOS skip it when `command -v python3` is `/usr/bin/python3` and `xcode-select -p` fails (installer-dialog stub); on Windows skip a `WindowsApps` path (Store stub).
   2. Else `uv`: run every script as `uv run --no-project python <script>`; uv downloads Python itself.
   3. Else stop and ask the user to install uv (https://docs.astral.sh/uv/getting-started/installation/) or Python.

   `node` is optional; without it cross-language checks report SKIP. Below, `python3` means `PY`.
1. **Ingest.** Read [references/ingest.md](references/ingest.md); follow the natural-language or uploaded-material rules.
2. **Design.** Read [references/interpretation.md](references/interpretation.md). Choose patterns, the template (Course routes), and conditional modules; define inputs, model, views, readouts, checks.
3. **Scaffold.**

   ```sh
   python3 scripts/new_topic.py <topic> <slug> \
     --template <template> --source prompt
   ```

   Templates are the directories under `templates/` (names in Course routes): layout and drawing JS, a runnable `model.py`, a notes skeleton, `TOPIC:` placeholders for prose. `examples/` holds two finished references. Templates and routes are optional starting points: when no template fits, or a different drawing serves the goal better, build the page from `Draft.*` primitives on a blank sheet; the same acceptance applies. Use `--source courseware` for uploaded material. The script copies the template, `build.py`, `check.py`, `bundle_notes.py`, `qa.py`, and shared assets into the topic, adding missing files without overwriting, so each topic is standalone and offline. `check.py` WARNs `unadapted template file` until model, page, and notes are rewritten. Changing `--template` does not migrate an existing topic; `--main` and `--sub` change only the title. `--lang <BCP47>` (default `en`, e.g. `zh-CN`, `ja`) sets `<html lang>`, which selects the CJK font stacks; write notes in the same language.
4. **Write the model and page.** Read [references/html-lab.md](references/html-lab.md) and [references/recipe.md](references/recipe.md); read [references/surface3d.md](references/surface3d.md) only for a native surface. Replace model, independent reference cases, and views. Replace every `{{…}}` and `TOPIC:` placeholder or delete its module. Adapt model, page, figures, and notes together; a new title does not adapt a topic.
5. **Create figures and notes.** Read [references/figures.md](references/figures.md). Write original notes from the template's `notes/` skeleton, citing numbers from `figures.json`. Remove unused modules and image references.
6. **Build and accept.**

   ```sh
   python3 viz/build.py            # figures, bundle, check
   python3 viz/qa.py               # HTTP: 1440 + 390; file://: 1440; or build.py --qa
   ```

   `--no-figures` skips `figures.py`; `--no-node` skips the Python/JavaScript comparison. Declare topic interactions in `viz/qa.json`, then follow [references/acceptance.md](references/acceptance.md) for screenshot review, repair scope, and stopping criteria.

## Deliverable gates

Deliver when the required checks in [references/acceptance.md](references/acceptance.md) pass; optional visual polish does not block delivery:

- `viz/build.py` reports 0 errors; each WARN and SKIP is resolved or reported.
- Browser inspection passes over HTTP at 1440px and 390px, plus an offline `file://` check at 1440px; content and controls remain readable and usable.
- Content gates hold: consistent definitions and numbers, stated domains and check tolerances, a meaningful operation, labeled sources.

## Scope and limits

- Scope: undergraduate math methods and physics concepts (areas in [Course routes](references/interpretation.md#course-routes)). Reduce complex problems to an explicit teaching model; a one-line prompt does not guarantee a reliable complete course.
- Out of scope: engineering networks, plants, PFD/P&ID, SDS, equipment selection, real engineering design.
- Finished labs compute in the browser; authoring, plotting, verification, and bundling use Python/Node.
- Reuse and licensing: [interpretation.md](references/interpretation.md#sources-and-reuse).
- Do not publish automatically or call paid services.
