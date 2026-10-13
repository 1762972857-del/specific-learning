#!/bin/sh
# Repository self-test: scaffold every template and run check.py, check both
# examples (check.py also verifies bundles), run qa.py in a browser (SKIP without one), run the surface3d verifier, and
# run the bindSelected unit test, confirm check.py rejects a stale bundle, mismatched defaults, a bad reader tab,
# a lost data-tex quote, a missing referenced id and a duplicate id,
# and exercise viz/build.py on a scaffold and on a temp copy of an example.
# Never writes inside the repo. Needs python3 and node. Exits non-zero if any step fails.
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
TMP=$(mktemp -d "${TMPDIR:-/tmp}/sl-selftest.XXXXXX")
trap 'rm -rf "$TMP"' EXIT INT TERM
FAIL=0
PY="python3 -I"

step() { printf '\n== %s\n' "$1"; }
fail() { printf 'FAIL: %s\n' "$1"; FAIL=1; }

for dir in "$ROOT"/templates/*/; do
  name=$(basename "$dir")
  step "template $name: scaffold + check"
  dest="$TMP/$name"
  if ! $PY "$ROOT/scripts/new_topic.py" "$dest" "$name" --template "$name" >/dev/null; then
    fail "scaffold $name"; continue
  fi
  out=$(cd "$dest" && $PY viz/check.py) ; rc=$?
  printf '%s\n' "$out" | tail -n 1
  [ $rc -eq 0 ] && printf '%s\n' "$out" | grep -q '^0 error' || fail "check.py on template $name"
done

for dir in "$ROOT"/examples/*/; do
  name=$(basename "$dir")
  step "example $name: check (includes bundle freshness)"
  out=$(cd "$dir" && $PY viz/check.py) ; rc=$?
  printf '%s\n' "$out" | tail -n 1
  [ $rc -eq 0 ] && printf '%s\n' "$out" | grep -q '^0 error' || fail "check.py on example $name"
  # Bundle freshness (notes and figures) is checked by check.py itself.
done

step "new_topic.py --lang zh-CN --main: lang attribute, no latin class"
dest="$TMP/lang-zh"
$PY "$ROOT/scripts/new_topic.py" "$dest" zh --template taylor-expansion --lang zh-CN --main "泰勒展开" >/dev/null || fail "scaffold with --lang"
grep -q '<html lang="zh-CN"' "$dest/viz/zh.html" && grep -q '<h1>泰勒展开</h1>' "$dest/viz/zh.html" && ! grep -q 'class="latin"' "$dest/viz/zh.html" || fail "--lang/--main output"
$PY "$ROOT/scripts/new_topic.py" "$TMP/lang-en" en --template taylor-expansion --main "Taylor" >/dev/null && grep -q '<html lang="en"' "$TMP/lang-en/viz/en.html" && grep -q '<h1 class="latin">Taylor</h1>' "$TMP/lang-en/viz/en.html" || fail "ASCII --main keeps latin"

step "courseware scaffold ignores uploaded sources"
$PY "$ROOT/scripts/new_topic.py" "$TMP/courseware" cw --template taylor-expansion --source courseware >/dev/null || fail "scaffold courseware"
grep -qx 'sources/raw.md' "$TMP/courseware/.gitignore" && ! grep -q 'annotated' "$TMP/courseware/.gitignore" || fail "courseware .gitignore lacks sources/raw.md"

step "negative tests: check.py must reject broken topics"
# expect NAME 'edit command run in topic dir' 'message grep pattern'
expect() {
  dest="$TMP/neg-$1"
  $PY "$ROOT/scripts/new_topic.py" "$dest" neg --template double-slit >/dev/null || { fail "scaffold for $1"; return; }
  (cd "$dest" && eval "$2") || { fail "edit for $1"; return; }
  out=$(cd "$dest" && $PY viz/check.py) ; rc=$?
  if [ $rc -ne 0 ] && printf '%s\n' "$out" | grep -q "$3"; then echo "rejected: $1"; else printf '%s\n' "$out" | grep -E '^(ERROR|[0-9]+ error)'; fail "check.py did not reject: $1"; fi
}
expect "stale bundle" 'for f in notes/*.md; do echo "extra line" >> "$f"; done' 'ERROR.*stale viz/markdown-bundle.js'
expect "defaults mismatch" 'sed "s/\"d\": 8\./\"d\": 9./" viz/model.py > viz/m.tmp && mv viz/m.tmp viz/model.py && grep -q "\"d\": 9\." viz/model.py' 'ERROR.*DEFAULTS disagree.*d: page=8 model=9'
expect "reader tab key" 'sed "s/data-view=\"guide\"/data-view=\"guidx\"/" viz/neg.html > viz/n.tmp && mv viz/n.tmp viz/neg.html && grep -q guidx viz/neg.html' 'ERROR.*reader tab data-view guidx'
expect "lost data-tex quote" 'sed "s/data-tex=\"\\\\Delta=r_2-r_1\"/data-tex=\"\\\\Delta=r_2-r_1/" viz/neg.html > viz/n.tmp && mv viz/n.tmp viz/neg.html && ! grep -q "r_2-r_1\"" viz/neg.html' 'ERROR.*malformed attribute.*line 78'
expect "missing referenced id" 'sed "s/id=\"delta\"/id=\"deltx\"/" viz/neg.html > viz/n.tmp && mv viz/n.tmp viz/neg.html && grep -q deltx viz/neg.html' 'ERROR.*referenced id not in HTML: delta'
expect "duplicate id" 'sed "s/id=\"ifar\"/id=\"phase\"/" viz/neg.html > viz/n.tmp && mv viz/n.tmp viz/neg.html && grep -q "id=\"phase\"" viz/neg.html' 'ERROR.*duplicate id phase'

step "build.py: scaffold without figures, example copy with figures"
dest="$TMP/build-scaffold"
$PY "$ROOT/scripts/new_topic.py" "$dest" bld --template double-slit >/dev/null || fail "scaffold for build.py"
out=$(cd "$dest" && $PY viz/build.py --no-figures) ; rc=$?
printf '%s\n' "$out" | tail -n 1
[ $rc -eq 0 ] && printf '%s\n' "$out" | grep -q '^0 error' || fail "build.py --no-figures on scaffold"
# newton-viscosity figures.py is stdlib-only; cp -RL keeps the repo untouched.
copy="$TMP/build-example"
cp -RL "$ROOT/examples/newton-viscosity" "$copy" || fail "copy example for build.py"
out=$(cd "$copy" && $PY viz/build.py --no-node) ; rc=$?
printf '%s\n' "$out" | grep -E '^(== |[0-9]+ error)'
[ $rc -eq 0 ] && printf '%s\n' "$out" | grep -q '== figures: viz/figures.py' || fail "build.py with figures on example copy"
# A failing check must fail the build; a missing module without uv must print the uv command.
neg="$TMP/build-neg"
$PY "$ROOT/scripts/new_topic.py" "$neg" neg --template double-slit >/dev/null || fail "scaffold for build.py failure"
sed 's/"d": 8\./"d": 9./' "$neg/viz/model.py" > "$neg/m.tmp" && mv "$neg/m.tmp" "$neg/viz/model.py"
out=$(cd "$neg" && $PY viz/build.py --no-figures) ; rc=$?
if [ $rc -ne 0 ] && printf '%s\n' "$out" | grep -q 'ERROR.*DEFAULTS disagree'; then echo "rejected: failing check"; else fail "build.py exit status ignored a failing check"; fi
mkdir "$TMP/nobin"
sed -i.bak '1i\
import nonexistent_pkg_xyz' "$neg/viz/model.py" && rm "$neg/viz/model.py.bak"
out=$(cd "$neg" && PATH="$TMP/nobin" "$(command -v python3)" -I viz/build.py --no-figures --no-node 2>&1) ; rc=$?
if [ $rc -ne 0 ] && printf '%s\n' "$out" | grep -q 'uv run --no-project --with nonexistent_pkg_xyz python viz/check.py'; then echo "rejected: missing module without uv"; else printf '%s\n' "$out" | tail -n 5; fail "build.py without uv did not print the uv command"; fi

step "qa.py: scaffolded template and example copy in a browser (SKIP when unavailable)"
# Exit 2 means qa.py could not run (no playwright/uv/Chromium); that is a SKIP, not a failure.
qa_run() {
  out=$(cd "$2" && $PY viz/qa.py --out "$TMP/qa-$1" 2>&1) ; rc=$?
  case $rc in
    0) printf '%s\n' "$out" | grep '^qa: .*runs passed' ;;
    2) printf 'SKIP: qa.py on %s: %s\n' "$1" "$(printf '%s\n' "$out" | head -n 1)" ;;
    *) printf '%s\n' "$out" | tail -n 12; fail "qa.py on $1" ;;
  esac
}
qa_run template-linear-transform "$TMP/linear-transform"
qa_run example-newton-viscosity "$copy"

step "surface3d verifier"
node "$ROOT/scripts/verify_surface3d.cjs" || fail "verify_surface3d.cjs"

step "bindSelected unit test"
node "$ROOT/scripts/verify_selected.cjs" || fail "verify_selected.cjs"

echo
if [ $FAIL -eq 0 ]; then echo "selftest: all passed"; else echo "selftest: FAILED"; fi
exit $FAIL
