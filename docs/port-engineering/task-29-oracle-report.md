# Task 29 Focus Blur oracle report

`task-29-oracle-generator.mjs --check` passes against pinned CPU source,
canonical runtime, catalog, adapter registry, and factory identity. The six
public cases are byte-for-byte identical to the independently prepared future
fixture: default depth A/B, numeric minima/maxima, same-Surface alias, and
nonzero tiled/global coordinates. Each freezes dimensions, repeat identity,
finite count, full F32 and RGBA8 SHA-256, and five F32-bit probes. The paired
default cases produce different F32 hashes, proving call-order discrimination.

Eight direct ABI modes execute eight explicit no-default switch arms and freeze
ID/name separately from observed ABI spelling, named branch slot, scene/depth
identity, alias/copy ownership, write/null behavior, operation counters, and a
F32 witness. Modes 0-2 are the only permitted const-reference
forms: both canonical argument orders and the alias case. Modes 3-7 are
distinct by-value, mutable-reference, pointer, wrong-resource-order, and null
pointer candidates. Wrong-order is tied to `depthSource==0/then`, so it is not
a duplicate of the valid else mapping. By-value allocates and reads two
independent Surface copies (96 F32 lanes), proven non-aliasing. Pixel-equal
ABI negatives remain failures because their independently authenticated
structural signature is forbidden; they never fall through to a baseline.

Implementation tests must additionally execute every source-semantic mutation
from the frozen adversarial matrix: forced/swapped branch orders, scene/depth
misuse, 63/65/drop/duplicate samples, and missing/duplicated alpha reads.
Require declared == handled == observed, pairwise-distinct semantic signatures
excluding IDs/names/acceptance/results, exact switch-case census, source hashes
for dispatch/mix/copy/witness code, invalid-enum rejection, and frozen oracle
bytes unchanged under every C++ table/switch/witness tamper.

No repository or Git state was changed.
