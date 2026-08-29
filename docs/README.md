# service — Documentation

A single-file Python toolkit for managing a professional services catalog.
`clinamenic_service.xml` is the source of truth (packages, tiers, retainers,
add-on modules, pricing, testimonials, prior work); `service_processor.py`
validates, converts, reports on, charts, and edits it.

## Repository map

- `clinamenic_service.xml` — the catalog (source of truth)
- `service_processor.py` — all operations (validate / convert / report / chart / edit)
- `docs/` — this documentation

## Running

```bash
python service_processor.py validate --xml clinamenic_service.xml --check-ids
python service_processor.py convert --xml clinamenic_service.xml --format json --output catalog.json
python service_processor.py convert --xml clinamenic_service.xml --format csv  --output out/
```

All commands take `--xml`. Python 3 standard library only; `matplotlib`
optional, needed only for chart outputs. Full command reference: root `README.md`.
