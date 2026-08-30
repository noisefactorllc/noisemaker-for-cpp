# Port engineering record

The working record of the C++20 port: design briefs, independent design
reviews, structural censuses of the corpus, and the hermetic JS-golden oracle
generators that every parity test is built from.

This lived in a scratch directory during development and is kept here because
it is not disposable. The oracle generators in particular are the ground truth
the C++ implementation is checked against — each one drives the real,
unmodified JavaScript reference and emits a `--check`-deterministic fixture.

## Layout

| Path | Contents |
|---|---|
| `NEXT_CODING_AGENT_HANDOFF.md` | Live state: current git/checkout facts, measured test counts, and the open work queue. Its top block supersedes every older status block. **Start here.** |
| `REMAINING-WORK-ROADMAP.md` | Historical consolidated state **as of 2026-08-12** (it reports 131 typed programs against a corpus of 212). Its hazard write-ups are still worth reading; its counts are not current — take those from the handoff above. |
| `census/` | Authoritative per-program terminal blockers for the unported frontier |
| `derivatives/` | `dFdx`/`dFdy`/`fwidth` architecture, gap-closure proofs, and oracle |
| `wormhole/` | The scatter-pass port and its oracle |
| `fdlibm/` | V8-bit-exact transcendental port, measurements, and integration patch |
| `shift-primitive/` | Signed-arithmetic shift design and its 16M-comparison sweep |
| `future-precompute/` | Per-cluster oracles and precompute (grade, matrix, cheap unlocks) |
| `loopproof/` | Loop-proof shape study and cluster oracles |
| `builtins/` | `round`/`any`/`reflect` admission oracle |
| `task-*.md` | Per-task briefs, design reviews, and implementation reports |

## Reproducing an oracle

Every generator re-derives its fixture by executing the real JavaScript
authority, so reproducing one requires a `noisemaker-for-cpu` checkout.
`--check` regenerates the fixture in memory and compares it byte-for-byte
against the committed JSON, so a drifted oracle fails loudly rather than
silently re-baselining. `--check` writes nothing; `--write` is the only mode
that does.

The 52 generators locate the authority in two different ways, and the
invocation differs accordingly. All commands below are run from the
repository root.

### Generators that take `--cpu-root` (31 of 52)

These name the authority on the command line and additionally read two
environment variables **by name**:

- `NOISEMAKER_CPU_ROOT` — an immutable snapshot of the JS authority, outside
  this repository.
- `NOISEMAKER_FOR_CPU` — your live, editable `noisemaker-for-cpu` checkout.
  Thirty of the thirty-one refuse to run if this resolves to the same tree as
  `--cpu-root`; the point of the rule is that a fixture is never re-derived
  from the checkout you are currently editing.

```sh
export NOISEMAKER_CPU_ROOT=<immutable snapshot of noisemaker-for-cpu>
export NOISEMAKER_FOR_CPU=<your live noisemaker-for-cpu checkout>

node docs/port-engineering/mandelbrot-parity/mandelbrot_oracle_generator.mjs \
  --check --cpu-root "$NOISEMAKER_CPU_ROOT"
# mandelbrot oracle generator: ok

node docs/port-engineering/newton-parity/newton_oracle_generator.mjs \
  --check --cpu-root "$NOISEMAKER_CPU_ROOT"
# newton oracle: ok
```

`julia-parity/julia_oracle_generator.mjs` is the single exception in this
family: it requires `--cpu-root`, `NOISEMAKER_CPU_ROOT` and
`NOISEMAKER_FOR_CPU` to all name the *same* pinned snapshot.

```sh
NOISEMAKER_FOR_CPU="$NOISEMAKER_CPU_ROOT" \
node docs/port-engineering/julia-parity/julia_oracle_generator.mjs \
  --check --cpu-root "$NOISEMAKER_CPU_ROOT"
# julia oracle generator: ok
```

Most of this family also accept `--self-test`.

### Generators that resolve the authority by relative import (21 of 52)

These take no root flag and read no environment variable. They import the
authority through a fixed relative path, so the checkout has to sit exactly
where the import expects it. Nothing in this repository creates that
directory — you place it yourself, as a checkout, a copy, or a symlink. Two
layouts are in use:

- **Sibling of the repository root** (`../noisemaker-for-cpu`) — 9 generators:
  everything under `bitops/` and `bvec/`, plus all of `loopproof/` except
  `loopproof/oracle-a/`.
- **Inside the generator's own cluster directory** — 12 generators, e.g.
  `docs/port-engineering/wormhole/noisemaker-for-cpu` for the wormhole oracle.
  The generator's first `import … from '…/noisemaker-for-cpu/…'` line names
  the directory it means; resolve that path relative to the generator file.

```sh
# sibling layout
ls ../noisemaker-for-cpu/src/effects/catalog.js
node docs/port-engineering/bitops/grain-parity/grain_parity_oracle_generator.mjs --check
# Grain parity oracle ok (14 render cases, 6 direct uint fixtures, 11 mutations)

# in-cluster layout
ls docs/port-engineering/wormhole/noisemaker-for-cpu/src/effects/cpu/wormhole.js
node docs/port-engineering/wormhole/oracle/wormhole_oracle_generator.mjs --check
# wormhole oracle fixture ok (62 cases, 9 mutations)
```

### When `--check` reports provenance drift

Each generator hash-pins the authority files it imports and aborts with
`provenance drift` or `runtime drift` if any of them differs by a byte. That
is the barrier working, not a broken fixture: it means the authority you
supplied is not the revision that generator was frozen against. Several
generators in this tree pin revisions older than a current
`noisemaker-for-cpu` checkout and will report drift until pointed at the
matching revision. Re-point the authority; never re-baseline the fixture to
silence it.

## A note on the numbers

Some regenerable bulk was deliberately excluded when this record was moved
in-repo: a 124MB shift-primitive sweep dump, ~18MB of float input vectors, and
compiled probe binaries. Every report citing those still states its exact
figures, and every generator can rebuild its own inputs.
