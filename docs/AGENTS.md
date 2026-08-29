# service — Agent Guide

## Layout

Two-file toolkit: the XML catalog and the processor script. The processor's
subcommands (validate, convert, report, chart, edit) all accept `--xml`;
`validate --check-ids` additionally enforces consistent ID formats.

## Conventions observed

- Standard library only by default; matplotlib is an optional dependency for
  chart outputs (per root `README.md`).
- The XML file is the single source of truth — every downstream artifact is
  regenerated from it, never hand-maintained separately.

## How docs here are maintained

Root `README.md` documents the full command surface. Keep `docs/README.md`
in sync when subcommands change; copy commands from the script, never invent.

## Notes for agents

- Edits to the catalog belong in `clinamenic_service.xml` (via the processor's
  edit command), not in derived outputs.
- Verify subcommand names against `service_processor.py` before documenting.
