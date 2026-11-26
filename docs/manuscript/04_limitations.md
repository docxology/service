# Limitations

A parser warning can affect the exports even when the structure passes
validation. The Grants Program package's Design + Management tier contains a
base price with the literal value `Custom`. The numeric parser warns and substitutes zero,
which can then flow into the exports, price statistics, and price chart.
Interpret the amount against the XML before using it as a quote
[@clinamenic-catalog; @service-processor].

The XML writer reconstructs the catalog from parsed records when the CLI
deletes a service. This preserves the modeled structure of the remaining
catalog, while input comments and unmodeled elements can be lost and
normalized values can differ from the source. Keep the original and review
the diff before adopting the edited copy. The CLI's add and update
operations are placeholders [@service-processor].
