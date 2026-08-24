# service

A single-file Python toolkit for keeping a professional services catalog in one place. `clinamenic_service.xml` is the source of truth — packages, tiers, retainers, add-on modules, pricing, testimonials, prior work — and `service_processor.py` validates it, converts it, reports on it, charts it, and edits it.

The point is that pricing and offerings live in one structured, diffable file rather than scattered across proposals and spreadsheets, and every downstream artifact is regenerated from it.

## Requirements

Python 3 (standard library only). `matplotlib` is optional and needed only for the chart outputs.

```bash
pip install matplotlib
```

## Usage

All commands take `--xml` to point at the catalog file.

```bash
# Validate the catalog, and check that IDs follow a consistent format
python service_processor.py validate --xml clinamenic_service.xml --check-ids

# Convert to JSON, or to a set of CSVs
python service_processor.py convert --xml clinamenic_service.xml --format json --output catalog.json
python service_processor.py convert --xml clinamenic_service.xml --format csv  --output out/

# Reports: summary, prices, or full
python service_processor.py report --xml clinamenic_service.xml --type prices --output prices.json

# Charts and graph data
python service_processor.py visualize --xml clinamenic_service.xml --type prices     --output price_chart.png
python service_processor.py visualize --xml clinamenic_service.xml --type categories --output category_chart.png
python service_processor.py visualize --xml clinamenic_service.xml --type d3         --output graph.json

# Read and edit services in place
python service_processor.py crud --xml clinamenic_service.xml --operation list
python service_processor.py crud --xml clinamenic_service.xml --operation get    --service-id SVC-01
python service_processor.py crud --xml clinamenic_service.xml --operation update  --service-id SVC-01 --json-input patch.json --output clinamenic_service.xml
```

CSV conversion writes four files into the output directory: `services.csv`, `packages.csv`, `tiers.csv`, and `retainers.csv`.

## Data model

The XML is parsed into typed dataclasses: `ServiceCatalog` holds `Metadata`, a `Provider`, and a list of `Service` entries; each service carries `Offering`, `Package`, `Tier`, `Retainer`, and `AddOnModule` records. Pricing is modeled explicitly — `Price`, `RecurringPrice`, `RangeFee`, `TierPricing`, `RetainerPricing`, `ModulePricing`, and `Discount` — so flat fees, recurring retainers, and tiered rates stay distinguishable instead of collapsing into one number. `Testimonial`, `PreviousWork`, `ExampleWork`, and `ClientInfo` round out the catalog.

## Adapting it

Point `--xml` at your own catalog file. The schema is defined implicitly by the dataclasses at the top of `service_processor.py`; `clinamenic_service.xml` doubles as the worked example.
