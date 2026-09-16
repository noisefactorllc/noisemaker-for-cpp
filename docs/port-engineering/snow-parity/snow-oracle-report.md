# filter/snow:snow pixel-parity oracle

Source: `src/effects/adapters/snow.js` (3443 bytes, sha256 202e0dbf9b1b8e0e7278c87527d6e2b740eb0a23385115c4805a389caab96366)

21 cases, 7 source-anchor mutation probes.

## Cases

- `1x1-alpha-zero` (1x1, alpha=0, time=0.25, pause=0, density=50)
- `1x1-alpha-one` (1x1, alpha=1, time=0.25, pause=0, density=50)
- `3x1-time-zero` (3x1, alpha=0.5, time=0, pause=0, density=50)
- `1x3-pause-true` (1x3, alpha=0.5, time=0.6, pause=1, density=50)
- `4x3-pause-boundary-exact` (4x3, alpha=0.5, time=0.6, pause=0.5, density=50)
- `4x3-pause-boundary-just-above` (4x3, alpha=0.5, time=0.6, pause=0.500001, density=50)
- `4x3-pause-between-tenth-and-half` (4x3, alpha=0.5, time=0.6, pause=0.3, density=50)
- `5x7-density-zero` (5x7, alpha=0.75, time=0.9, pause=0, density=0)
- `5x7-density-negative` (5x7, alpha=0.75, time=0.9, pause=0, density=-10)
- `5x7-density-hundred` (5x7, alpha=0.75, time=0.9, pause=0, density=100)
- `5x7-density-above-range` (5x7, alpha=0.75, time=0.9, pause=0, density=250)
- `7x5-alpha-near-zero` (7x5, alpha=0.0001, time=1.75, pause=0, density=40)
- `7x5-alpha-above-one` (7x5, alpha=1.5, time=1.75, pause=0, density=40)
- `7x5-alpha-below-zero` (7x5, alpha=-0.5, time=1.75, pause=0, density=40)
- `9x2-cosine-just-above-epsilon` (9x2, alpha=0.6, time=1.75, pause=0, density=60)
- `2x9-cosine-near-half-turn` (2x9, alpha=0.6, time=0.5, pause=0, density=60)
- `2x9-cosine-near-full-turn` (2x9, alpha=0.6, time=1, pause=0, density=60)
- `17x11-default-like` (17x11, alpha=0.5, time=0.25, pause=0, density=75)
- `17x11-large-time` (17x11, alpha=0.5, time=137.375, pause=0, density=75)
- `11x17-transposed` (11x17, alpha=0.5, time=0.25, pause=0, density=75)
- `13x1-negative-time` (13x1, alpha=0.5, time=-3.5, pause=0, density=75)

## Mutation sensitivity

- `pause-threshold`: changed 2/21 cases (4x3-pause-boundary-exact, 4x3-pause-between-tenth-and-half)
- `static-seed-x`: changed 17/21 cases (1x1-alpha-one, 3x1-time-zero, 1x3-pause-true, 4x3-pause-boundary-exact, 4x3-pause-boundary-just-above, 4x3-pause-between-tenth-and-half, 5x7-density-hundred, 5x7-density-above-range, 7x5-alpha-near-zero, 7x5-alpha-above-one, 9x2-cosine-just-above-epsilon, 2x9-cosine-near-half-turn, 2x9-cosine-near-full-turn, 17x11-default-like, 17x11-large-time, 11x17-transposed, 13x1-negative-time)
- `limiter-seed-x`: changed 16/21 cases (1x1-alpha-one, 3x1-time-zero, 1x3-pause-true, 4x3-pause-boundary-exact, 4x3-pause-boundary-just-above, 4x3-pause-between-tenth-and-half, 5x7-density-above-range, 7x5-alpha-near-zero, 7x5-alpha-above-one, 9x2-cosine-just-above-epsilon, 2x9-cosine-near-half-turn, 2x9-cosine-near-full-turn, 17x11-default-like, 17x11-large-time, 11x17-transposed, 13x1-negative-time)
- `density-scale`: changed 17/21 cases (1x1-alpha-one, 3x1-time-zero, 1x3-pause-true, 4x3-pause-boundary-exact, 4x3-pause-boundary-just-above, 4x3-pause-between-tenth-and-half, 5x7-density-hundred, 5x7-density-above-range, 7x5-alpha-near-zero, 7x5-alpha-above-one, 9x2-cosine-just-above-epsilon, 2x9-cosine-near-half-turn, 2x9-cosine-near-full-turn, 17x11-default-like, 17x11-large-time, 11x17-transposed, 13x1-negative-time)
- `limiter-cap`: changed 15/21 cases (1x1-alpha-one, 3x1-time-zero, 4x3-pause-boundary-exact, 4x3-pause-boundary-just-above, 4x3-pause-between-tenth-and-half, 5x7-density-above-range, 7x5-alpha-near-zero, 7x5-alpha-above-one, 9x2-cosine-just-above-epsilon, 2x9-cosine-near-half-turn, 2x9-cosine-near-full-turn, 17x11-default-like, 17x11-large-time, 11x17-transposed, 13x1-negative-time)
- `time-seed-offset-x`: changed 14/21 cases (1x1-alpha-one, 4x3-pause-boundary-exact, 4x3-pause-between-tenth-and-half, 5x7-density-hundred, 5x7-density-above-range, 7x5-alpha-near-zero, 7x5-alpha-above-one, 9x2-cosine-just-above-epsilon, 2x9-cosine-near-half-turn, 2x9-cosine-near-full-turn, 17x11-default-like, 17x11-large-time, 11x17-transposed, 13x1-negative-time)
- `zbase-epsilon`: changed 3/21 cases (7x5-alpha-near-zero, 7x5-alpha-above-one, 9x2-cosine-just-above-epsilon)
