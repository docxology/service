# AGENTS.md — service

Guidance for agents working in this repository.

## What this repository is

A single-file Python toolkit for keeping a professional services catalog in one place.
`clinamenic_service.xml` is the source of truth — packages, tiers, retainers, add-on modules,
pricing, testimonials and prior work — and `service_processor.py` validates it, converts it,
reports on it, charts it and edits it. Every downstream artifact is regenerated from the XML
rather than hand-maintained, which is the whole point of the arrangement.

## Commands

Python 3.9 or newer, standard library only. `matplotlib` is optional and needed only for the
chart outputs (`pip install matplotlib`). Every subcommand takes `--xml`.

```bash
python service_processor.py validate  --xml clinamenic_service.xml --check-ids
python service_processor.py convert   --xml clinamenic_service.xml --format json --output catalog.json
python service_processor.py convert   --xml clinamenic_service.xml --format csv  --output out/
python service_processor.py report    --xml clinamenic_service.xml --type prices --output prices.json
python service_processor.py visualize --xml clinamenic_service.xml --type prices --output price_chart.png
python service_processor.py crud      --xml clinamenic_service.xml --operation list
```

CSV conversion writes four files into the output directory: `services.csv`, `packages.csv`,
`tiers.csv` and `retainers.csv`.

## Layout

| Path | Role |
|---|---|
| `clinamenic_service.xml` | The catalog, and the worked example of its own schema |
| `service_processor.py` | Every subcommand; the schema is defined implicitly by the dataclasses at the top |
| `docs/AGENTS.md` | Notes on the `docs/` folder itself |

## Things that are easy to get wrong

- **Service IDs are numeric** (`1`, `2`, `3`). `--check-ids` additionally enforces package IDs
  of the form `service_id.n` and tier IDs of the form `service_id.package_num.tier_num`.
- **`crud --operation add` and `--operation update` are accepted but not implemented.** They
  print a notice and write no file. Do not document them as working, and do not treat their
  successful parse as success.
- **Edits belong in the XML**, through `crud`, not in derived JSON, CSV or chart outputs.
- Pricing is modelled explicitly (`Price`, `RecurringPrice`, `RangeFee`, `TierPricing`,
  `RetainerPricing`, `ModulePricing`, `Discount`) so flat fees, recurring retainers and tiered
  rates stay distinguishable. Collapsing them into one number is a data-loss bug.

## Working here

- Verify subcommand names and flags against `service_processor.py` before writing them down.
- There is no test suite and no CI workflow, so a change is only as verified as the command you
  ran. Report the exact command and its output.

## Relationship to `docs/AGENTS.md`

`docs/AGENTS.md` documents the `docs/` folder only. This file is the repository-level entry
point; the two should not restate each other.
