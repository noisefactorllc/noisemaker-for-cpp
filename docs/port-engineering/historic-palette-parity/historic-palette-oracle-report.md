# Historic Palette exact-pixel oracle

- Program: filter/historicPalette:historicPalette
- Authority: unmodified public canonical historicPaletteFactory from an immutable CPU snapshot.
- Cases: 21; exact mutation ledger entries: 6.
- The closure is transitively discovered, hash-pinned and realpath-confined.
- Every palette index plus smoothness, wrap, rotation, fract, alpha, storage and comparer controls is covered.

## Reproduction

node docs/port-engineering/historic-palette-parity/historic_palette_oracle_generator.mjs --check --cpu-root "$NOISEMAKER_CPU_ROOT"
python3 -B tools/glslcpp/generate_historic_palette_native_oracle_include.py --check

Absolute checkout paths are intentionally omitted from this report and JSON.
