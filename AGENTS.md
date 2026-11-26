# AGENTS.md — service

`service_processor.py` defines the data model, parsers, exporters and CLI.
`clinamenic_service.xml` is the worked catalog. Make catalog edits in XML
and regenerate derived files as needed.

- [User guide](docs/README.md) documents the CLI and its current limitations.
- [Manuscript guide](docs/manuscript/README.md) documents the build workflow.

There is no test suite or CI workflow. Verify changes through the relevant
CLI commands, read warnings and validation messages, and inspect generated
artifacts. Use a separate output file for destructive catalog examples.
