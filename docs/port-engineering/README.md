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
| `REMAINING-WORK-ROADMAP.md` | Consolidated state: what is ported, what remains, and every standing hazard. **Start here.** |
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

Each generator is hermetic and self-checking. From the repository root:

```sh
node docs/port-engineering/<cluster>/<name>_oracle_generator.mjs --check
```

`--check` regenerates the fixture in memory and compares it byte-for-byte
against the committed JSON, so a drifted oracle fails loudly rather than
silently re-baselining.

## A note on the numbers

Some regenerable bulk was deliberately excluded when this record was moved
in-repo: a 124MB shift-primitive sweep dump, ~18MB of float input vectors, and
compiled probe binaries. Every report citing those still states its exact
figures, and every generator can rebuild its own inputs.
