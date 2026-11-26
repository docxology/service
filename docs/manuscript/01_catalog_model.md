# Catalog model

The example catalog contains separate Governance, Knowledge, and Branding
services. Each service includes metadata and provider information. Its
offering can contain packages and retainers. Package tiers can describe
deliverables, base prices and discounts. Retainer pricing can carry a
recurring amount, its frequency and a minimum term. The bundled Knowledge
offering also shows how add-on modules represent pricing forms such as a
range fee or a custom quote [@clinamenic-catalog].

The processor reads the document with Python's ElementTree module
[@elementtree]. It retains the default namespace for serialization and
strips namespace prefixes from element tags before the dataclass parsers
look up their children. A service's ID links it to its package and retainer
rows. Package IDs provide a second link to tier rows
[@service-processor].
