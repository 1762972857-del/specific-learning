# Specific Learning

[![CI](https://github.com/1762972857-del/specific-learning/actions/workflows/ci.yml/badge.svg)](https://github.com/1762972857-del/specific-learning/actions/workflows/ci.yml)

**English** | [简体中文](README.zh-CN.md)

Turn an undergraduate math or physics concept into an interactive, offline lab with original figures and readable Markdown notes. Start from a natural-language question or uploaded course material. Natural-language topics are checked against authoritative university lectures or public technical references before the teaching model is written.

The visual system uses warm paper, ink, orange selections and blue regions. Controls stay beside the experiment on desktop and move above it on small screens. Equations render locally with KaTeX. Optional 3D surfaces use the project's small native Canvas renderer.

## Two finished examples

These are complete reference deliverables: notes, figures, model and page. Open their HTML files from a local clone, or serve the repository with `python3 -m http.server`.

### Taylor expansion

[Open the lab](examples/taylor-expansion/viz/taylor-expansion.html) · [Read the guide](examples/taylor-expansion/notes/01-taylor-expansion.md)

Drag polynomial degree and compare the local fit, partial sums and approximation error.

![Dragging the degree changes the Taylor approximation](docs/demos/taylor-expansion.gif)

### Newton's law of viscosity

[Open the lab](examples/newton-viscosity/viz/newton-viscosity.html) · [Read the guide](examples/newton-viscosity/notes/01-viscosity.md)

Change the moving plate speed or fluid properties and connect the velocity gradient to shear stress.

![Dragging plate speed changes fluid flow and shear stress](docs/demos/newton-viscosity.gif)

## Templates

Six slim starting points live in `templates/`. They provide page layout, drawing and interaction code, a runnable `model.py` and a notes skeleton with `TOPIC:` placeholders; they are not content.

| Template | Starting point for |
| --- | --- |
| `taylor-expansion` | Approximation vs target, error against a parameter, draggable expansion point |
| `barrier-tunneling` | Piecewise 1D regions, wave density, conservation readouts |
| `partial-derivatives` | Native 3D surface with slices, tangent slopes and finite differences |
| `newton-viscosity` | Time evolution with a fixed-step clock, schematic and profile |
| `double-slit` | Cached 2D intensity/amplitude heatmap, path-difference schematic, screen profile |
| `linear-transform` | Equal-scale grid mapping with draggable basis vectors, determinant and eigen-directions |

## Install

### Skills CLI (recommended)

Use the [Skills CLI](https://github.com/vercel-labs/skills) with Node.js (npm/npx) and Git installed. Install for the agents you use:

| Command | Installs to |
| --- | --- |
| `npx skills@latest add 1762972857-del/specific-learning -g -a claude-code` | `~/.claude/skills/specific-learning` (symlink to the shared copy) |
| `npx skills@latest add 1762972857-del/specific-learning -g -a codex` | `~/.agents/skills/specific-learning` |
| `npx skills@latest add 1762972857-del/specific-learning -g -a opencode` | `~/.agents/skills/specific-learning` |
| `npx skills@latest add 1762972857-del/specific-learning -g -a cursor` | `~/.agents/skills/specific-learning` |
| `npx skills@latest add 1762972857-del/specific-learning -g` | Global installation; choose agents when prompted |
| `npx skills@latest add 1762972857-del/specific-learning` | Current project: `.agents/skills/specific-learning`; Claude Code also gets a `.claude/skills/specific-learning` entry when selected |

Paths describe the default symlink mode, verified with Skills CLI 1.7.2. Codex, OpenCode, and Cursor use the shared `.agents/skills` directory in this mode. `-g` makes the skill available across projects; without it, run from your target project root. Repeat `-a` to select multiple agents, or add `--copy` for independent copies in agent-specific directories.

Private repositories use your existing Git, authenticated GitHub CLI, or SSH access. If using SSH, replace the repository argument with `git@github.com:1762972857-del/specific-learning.git`. The installing account must have repository access; no token belongs in this repository.

List and update global installations with:

```sh
npx skills@latest list --global
npx skills@latest update specific-learning --global
```

For an existing manual installation, keep your development checkout and any local edits outside the managed skill directory before switching. The CLI manages installed copies, not your development checkout.

### Manual installation

For development or installation without the CLI, clone the repository:

```sh
git clone https://github.com/1762972857-del/specific-learning.git
cd specific-learning
```

Put or symlink the whole directory into your agent's skill directory, such as `~/.agents/skills/specific-learning` for Codex or `~/.claude/skills/specific-learning` for Claude Code. Keep `SKILL.md`, `references/`, `assets/`, `scripts/`, `templates/` and `examples/` together; the skill reads them by relative path. The Skills CLI also installs these resources; there is no separate npm package for this skill.

Authoring needs the following; readers of a finished lab need only a browser.

| Missing | Effect | Fix |
| --- | --- | --- |
| Python (`python3`) | Scaffold and build blocked | Install [uv](https://docs.astral.sh/uv/getting-started/installation/); run scripts as `uv run --no-project python <script>` |
| Node.js | Skills CLI installation is unavailable; Python/JavaScript and DEFAULTS checks report SKIP | Install Node.js with npm/npx, or install the skill manually and accept skipped model comparisons |
| NumPy / matplotlib | Only figures that use them fail | `viz/build.py` retries through uv |
| Browser automation (Playwright) | `viz/qa.py` cannot run; inspect by hand | Optional; `qa.py` retries through uv, or use host browser tools |

## How to use

After installation, open your coding agent in a project and ask in natural language:

```text
Explain Taylor expansion.
Visualize a linear transformation.
Turn the uploaded lecture notes into an interactive lab and learning notes.
```

Add your level, preferred language, or focus when useful, such as “show how the matrix columns are weighted by the input vector.” If the agent does not select the skill automatically, start with “Use the specific-learning skill to…”. It creates an HTML lab and Markdown notes; open the generated HTML in your browser to explore.

### Scaffold manually

The entry point is [SKILL.md](SKILL.md). The scaffold copies real files into the output, so each generated topic is portable.

From the skill directory:

```sh
python3 scripts/new_topic.py /tmp/my-taylor my-taylor \
  --template taylor-expansion --source prompt
```

Template choices are the directories under `templates/` (see the table above). Use `--source courseware` for uploaded materials; this adds a `sources/` directory. Optional `--lang <BCP47>` (default `en`, for example `zh-CN`) sets `<html lang>`; write the notes in the same language. Optional `--main` and `--sub` change the visible title, not the lesson's model. Adapt the model, figures, page and notes together. Existing files are preserved when the command is repeated.

## Viewing and authoring

**Readers need only a browser.** Finished labs include local KaTeX, marked, fonts and bundled notes/figures. They work without a network connection or Python installation.

**Authoring tools** are listed under Install. The build script, checker, scaffold and Markdown bundler use only Python's standard library; `qa.py` additionally needs Playwright.

From a generated topic's root:

```sh
python3 viz/build.py              # figures (if any), notes bundle, checks
python3 viz/build.py --no-figures # skip figures.py; --no-node skips the Python/JS comparison
python3 viz/qa.py                 # browser acceptance (or build.py --qa)
python3 -m http.server            # open the page in a browser
```

`build.py` stops at the first failing step and exits with `check.py`'s status. If `figures.py` or `check.py` needs a package such as NumPy that the current Python lacks, it retries that step through `uv run --no-project` (using the topic's `requirements.txt` when present); without `uv` it prints the exact command. It never installs into the system Python.

Each template documents its own extra checks. These verify reference cases, boundaries and implementation agreement; they do not prove all inputs or replace mathematical reasoning. Consult the Guide for assumptions, units, numerical limits and direct source links.

## Repository layout

| Location | Responsibility |
| --- | --- |
| `SKILL.md`, `references/` | Workflow, source rules and rendering/model contracts |
| `assets/` | Shared styles, drawing helpers, optional 3D renderer and local vendors |
| `examples/` | Two finished reference deliverables (`taylor-expansion`, `newton-viscosity`): model, figures, guide and page |
| `templates/` | Six slim layout and drawing starting points (page, model, notes skeleton) |
| `scripts/new_topic.py` | Scaffold a standalone topic from a template |
| `scripts/build.py` | One-command build: figures, bundle, check, with a `uv` fallback for missing packages |
| `scripts/qa.py` | Browser acceptance with Playwright: HTTP at 1440px and 390px, `file://` at 1440px, reader, screenshots; topic steps in `viz/qa.json` |
| `scripts/check.py` | Known-result, cross-language and structural checks |
| `scripts/bundle_notes.py` | Bundle Markdown and figures for offline reading |
| `scripts/selftest.sh` | Repository self-test: scaffold every template, check examples, surface renderer, bundle freshness |
| `docs/demos/` | GIF recordings of actual browser interaction |

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for repository roles, adding templates and the self-test. Private deliveries, local handoff notes, caches and environments are excluded by `.gitignore`.

University resources are cited for verification; their source documents are not redistributed as part of these examples.

## License

MIT; see [LICENSE](LICENSE). The vendored KaTeX and marked libraries under `assets/vendor/` keep their own MIT licenses.
