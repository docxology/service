# service user guide

[The Clinamenic catalog](../clinamenic_service.xml) is the maintained input.
[The processor](../service_processor.py) reads packages, tiers, retainers and
other catalog records from XML and generates views of those records for
different uses.

- [Setup and catalog selection](#setup-and-catalog-selection)
- [Validate a catalog](#validate-a-catalog)
- [Generate outputs](#generate-outputs)
- [Inspect and edit a catalog](#inspect-and-edit-a-catalog)
- [Technical manuscript and build instructions](manuscript/README.md)

## Setup and catalog selection

Use Python 3.9 or newer. Core commands use the standard library. To generate
PNG charts, install matplotlib in a virtual environment.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install matplotlib
```

Run the examples from the repository root. Every subcommand accepts
`--xml PATH` and defaults to `clinamenic_service.xml` in the current directory.
To adapt the catalog, copy the bundled XML and point `--xml` at your copy.
The dataclasses and their XML parsers in the processor define the accepted
structure. Use the bundled `Services` root and its `Service` entries as a
worked example. Each service has metadata, a provider, and an offering
with packages, tiers, or retainers. The pricing model distinguishes base
prices, recurring prices, range fees, discounts, and custom quotes where
the relevant record supports them.

## Validate a catalog

```bash
python3 service_processor.py validate --xml clinamenic_service.xml --check-ids
```

Basic validation checks missing service names and missing or duplicate IDs
among services, packages within a service, and tiers within a package.
`--check-ids` adds positive integer checks for service IDs and verifies the
segment counts and parent prefixes for package and tier IDs
(`service_id.n` and `service_id.package_num.tier_num`). The package and tier
checks allow nonnumeric suffixes.

Read the console output as well as the exit status. Parse or validation
findings can be printed without a failing exit status. For the bundled
catalog, expect Governance, Knowledge, and Branding to load and both
validation summaries to report success. The parser also warns that the
`Custom` base price on the Grants Program package’s Design + Management tier is converted to
`0.0`. Check the XML before interpreting that value as an actual quote.

## Generate outputs

Create a temporary destination before running the file-based commands.

```bash
service_output="$(mktemp -d)"
python3 service_processor.py convert --xml clinamenic_service.xml --format json --output "$service_output/catalog.json"
python3 service_processor.py convert --xml clinamenic_service.xml --format csv --output "$service_output/csv"
python3 service_processor.py report --xml clinamenic_service.xml --type prices --output "$service_output/prices.json"
python3 service_processor.py visualize --xml clinamenic_service.xml --type d3 --output "$service_output/hierarchy.json"
```

- **JSON export** contains services, packages and tiers, and retainers.
  It includes tier base amounts and currencies, plus recurring amounts,
  currencies and frequencies for priced retainers. It omits discounts,
  add-on modules, testimonials and prior work.
- **CSV export** writes `services.csv`, `packages.csv`, `tiers.csv` and
  `retainers.csv`. Match package and retainer rows to services by
  `Service ID`, and tier rows to packages by `Package ID`.
- **Reports** support `summary` (default), `prices`, and `full`.
  Reports print to the console and optionally save to the path given with
  `--output`. The price report groups base tier and recurring retainer
  amounts separately, with per-currency statistics and a headline range and
  average for the most common currency in each group.
- **D3 JSON** contains a service–package–tier hierarchy, with tier base
  amounts when present. It contains no retainer hierarchy or currency labels.

With matplotlib installed, use `visualize --type prices` or
`visualize --type categories`.

```bash
MPLBACKEND=Agg python3 service_processor.py visualize --xml clinamenic_service.xml --type prices --output "$service_output/price_chart.png"
MPLBACKEND=Agg python3 service_processor.py visualize --xml clinamenic_service.xml --type categories --output "$service_output/category_chart.png"
```

The price chart shows tier base amounts in the most common tier currency.
The category chart counts services by category. Verify the expected files
exist and open the images before relying on them. For JSON, try
`python3 -m json.tool "$service_output/catalog.json"`, then compare a service
and one tier against the XML.

## Inspect and edit a catalog

The CLI implements `list`, `get` and `delete`. Use a separate destination
for deletion, then validate the result and review the XML diff before
replacing the source.

```bash
python3 service_processor.py crud --xml clinamenic_service.xml --operation list
python3 service_processor.py crud --xml clinamenic_service.xml --operation get --service-id 1
python3 service_processor.py crud --xml clinamenic_service.xml --operation delete --service-id 1 --output "$service_output/edited.xml"
python3 service_processor.py validate --xml "$service_output/edited.xml" --check-ids
diff -u clinamenic_service.xml "$service_output/edited.xml"
```

Deletion regenerates XML from parsed dataclasses. Formatting, comments,
unmodeled XML, and values normalized by the parser may change. The CLI
accepts `add` and `update` as placeholders. They print a notice and do not
write an output file, even if `--json-input` and `--output` are supplied.
