# filter/median:median all-radii pixel-parity oracle

Source: `src/effects/adapters/median.js` (5349 bytes, sha256 e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583)

19 cases, 7 source-anchor mutation probes.

Supersedes nothing -- the original median_oracle_generator.mjs / median-oracles.json package in this directory is kept as evidence. This package additionally covers radius 1 and 3 (not just 2), sizes smaller than the kernel window, ties/duplicate records at two different comparator levels, a translucent-alpha ramp, HDR and negative channel values, a NaN channel, and a threshold sweep.

## Cases

- `r1-3x3-window-exact` (3x3, radius=1, threshold=0)
- `r1-1x1-heavy-clamp` (1x1, radius=1, threshold=0)
- `r2-5x5-window-exact` (5x5, radius=2, threshold=0)
- `r2-2x2-heavy-clamp` (2x2, radius=2, threshold=0)
- `r2-7x4-nonsquare` (7x4, radius=2, threshold=0)
- `r3-7x7-window-exact` (7x7, radius=3, threshold=0)
- `r3-3x3-heavy-clamp` (3x3, radius=3, threshold=0)
- `r3-9x5-nonsquare` (9x5, radius=3, threshold=0)
- `r3-1x9-strip` (1x9, radius=3, threshold=0)
- `r2-9x11-transposed` (9x11, radius=2, threshold=0)
- `r2-ties-checkerboard` (6x6, radius=2, threshold=0)
- `r1-ties-redgreen-tiebreak` (3x3, radius=1, threshold=0)
- `r2-translucent-ramp` (5x4, radius=2, threshold=0)
- `r1-hdr-and-negative` (3x3, radius=1, threshold=0)
- `r2-nan-channel` (3x3, radius=2, threshold=0)
- `r3-nan-with-threshold` (3x3, radius=3, threshold=50)
- `r2-threshold-zero` (4x4, radius=2, threshold=0)
- `r2-threshold-mid` (4x4, radius=2, threshold=12)
- `r2-threshold-hundred` (4x4, radius=2, threshold=100)

## Mutation sensitivity

- `luminance-red-weight`: changed 10/19 cases (r1-3x3-window-exact, r2-5x5-window-exact, r3-7x7-window-exact, r3-3x3-heavy-clamp, r3-9x5-nonsquare, r2-9x11-transposed, r2-translucent-ramp, r2-nan-channel, r2-threshold-zero, r2-threshold-mid)
- `luminance-green-weight`: changed 5/19 cases (r2-7x4-nonsquare, r3-7x7-window-exact, r1-hdr-and-negative, r2-threshold-zero, r2-threshold-mid)
- `half-round-bias`: changed 10/19 cases (r2-5x5-window-exact, r2-7x4-nonsquare, r3-7x7-window-exact, r3-9x5-nonsquare, r3-1x9-strip, r2-9x11-transposed, r2-translucent-ramp, r1-hdr-and-negative, r2-threshold-zero, r2-threshold-mid)
- `median-index-formula`: changed 15/19 cases (r1-3x3-window-exact, r2-5x5-window-exact, r2-7x4-nonsquare, r3-7x7-window-exact, r3-3x3-heavy-clamp, r3-9x5-nonsquare, r2-9x11-transposed, r2-ties-checkerboard, r1-ties-redgreen-tiebreak, r2-translucent-ramp, r1-hdr-and-negative, r2-nan-channel, r3-nan-with-threshold, r2-threshold-zero, r2-threshold-mid)
- `threshold-divisor`: changed 2/19 cases (r3-nan-with-threshold, r2-threshold-mid)
- `half-exponent-bias`: changed 19/19 cases (r1-3x3-window-exact, r1-1x1-heavy-clamp, r2-5x5-window-exact, r2-2x2-heavy-clamp, r2-7x4-nonsquare, r3-7x7-window-exact, r3-3x3-heavy-clamp, r3-9x5-nonsquare, r3-1x9-strip, r2-9x11-transposed, r2-ties-checkerboard, r1-ties-redgreen-tiebreak, r2-translucent-ramp, r1-hdr-and-negative, r2-nan-channel, r3-nan-with-threshold, r2-threshold-zero, r2-threshold-mid, r2-threshold-hundred)
- `tiebreak-redgreen-direction`: changed 1/19 cases (r1-ties-redgreen-tiebreak)
