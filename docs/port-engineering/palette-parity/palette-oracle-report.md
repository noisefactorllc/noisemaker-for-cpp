# Palette pixel oracle

This package freezes the direct/public filter/palette:palette CPU adapter from an immutable authority snapshot. It covers passthrough, RGB/HSV/OkLab routes, alpha, offset/repeat, both rotation directions, tile metadata, and input immutability.

- Cases: 8
- Semantic mutation witnesses: 13
- Comparison: exact little-endian Float32 words and exact RGBA8 bytes.
