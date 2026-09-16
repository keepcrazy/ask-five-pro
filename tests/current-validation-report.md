# Ask Five Pro refactor validation report

Date: 2026-09-16
Change: `refactor-ask-five-pro`
Compatibility baseline: `4627911`

## Result

Local refactor compatibility validation: **PASS**

Real host meeting validation: **NOT RUN / NOT VERIFIED**

The local result proves the repository contracts, scripts, fixtures, packaged
assets, and temporary-install behavior described below. It does not prove that
a particular external host will trigger or render the Skill identically.

## Directory changes

- Root `SKILL.md` now contains the complete normative workflow.
- References are limited to mode templates, output examples, anti-patterns,
  and fallback profiles.
- Expert Registry, Flash profiles, packs, matching core, Query adapter, and
  asset validator live under `brain-crew/`.
- Historical reports, outputs, obsolete Engine tools, and old quality
  evaluations live under `tests/evidence/` and do not participate in the
  current gate.
- Active fixtures and tests live under `tests/fixtures/` and `tests/test_*.py`.

## Duplicate logic convergence

- The only Registry is `brain-crew/expert-registry.json`.
- `references/expert-registry.json`, its `.bak`, and old-path redirects are
  absent.
- `scripts/match-experts.py` and
  `brain-crew/scripts/brain_crew_query.py` call
  `brain-crew/scripts/matching_core.py`.
- Query API public functions remain available, but it contains no second
  scoring formula.

## Approved conflict resolutions

The implementation is checked against the 24-entry allowlist at
`tests/fixtures/baseline/conflict-allowlist.json`.

The only approved matching-result corrections are:

1. team/organization, technology/engineering, and risk/risk-control aliases;
2. sensitive experts excluded by default and eligible only when explicitly
   named or in debate mode.

Boundary Guard retains the v2.2.3 fixed scan order and first-match result.
Roster confirmation, persona loading, meeting orchestration, synthesis, and
seven-part output remain Skill/host responsibilities.

## Expert source-file restoration and verification

- Registry experts: 40/40
- Pack distribution: core 6, brand 10, tech 7, enterprise 12, meta 5
- Flash profiles: 40/40
- Fixed-source files restored/compared: 46
- Missing, duplicate, orphaned, or modified expert source assets: 0
- Model-written expert repairs: 0

All bundled expert source files match the immutable local Git source snapshot
at `4627911`. This checkout has no configured remote, so the local Git commit
is the recorded fixed source.

## Current validation

| Gate | Result |
|---|---|
| `python3 tests/run-validation.py` | PASS, 41 tests |
| Boundary baseline field comparison | PASS |
| CLI/Query shared matching and approved-difference checks | PASS |
| Registry normalization and three-identifier contract | PASS |
| Full expert source comparison | PASS |
| Missing-asset negative gate | PASS |
| Temporary installation without external Brain Crew | PASS |
| External-cwd asset validation | PASS |
| Aggregate failure returns non-zero | PASS |
| Registry replacement restores on success/failure/exception | PASS |
| Migration map coverage, 145 unique baseline dispositions | PASS |
| Unchanged `keep`/`move` targets match baseline blobs | PASS, 0 differences |
| Conflict allowlist coverage and manual review, 24 decisions | PASS |
| Baseline fixture regeneration with fixed hash seed | PASS, repeatable |
| `openspec validate refactor-ask-five-pro --strict` | PASS |
| `git diff --check` | PASS |
| Shell syntax and Registry JSON parsing | PASS |
| Forbidden runtime controller scan | PASS |

## Breaking change

Calls to `references/expert-registry.json` now fail. Consumers must migrate to
`brain-crew/expert-registry.json`; no compatibility wrapper or redirect is
provided.
