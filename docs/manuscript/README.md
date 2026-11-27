# Service catalog technical manuscript

This directory contains the canonical source for *Maintaining a Professional
Services Catalog in XML*. The renderer reads the numbered sections in order,
uses `config.yaml` and `preamble.md` for rendering, and resolves citations
from `references.bib`. The workflow figure describes the processor's data
flow. Its PNG and editable Graphviz source live in [assets](assets/).

To regenerate the image after changing the source, run Graphviz from this
directory.

```bash
dot -Tpng assets/catalog-workflow.dot -o assets/catalog-workflow.png
```

## Render and validate

Use a clean Git checkout named `service` and a separate copy of the
[pinned template](https://github.com/docxology/template/tree/87704feae0a4490ef7dad9c931d268e8c30273c2).
Install Git, uv, Pandoc, XeLaTeX, and the TeX prerequisites in the template's
[setup guide](https://github.com/docxology/template/blob/87704feae0a4490ef7dad9c931d268e8c30273c2/docs/guides/startup-and-setup.md).
The manuscript render uses the checked-in diagram and requires no chart
generation. For native catalog commands, see the [user guide](../README.md).

Run the following from the root of the service checkout.

```bash
service_checkout="$(pwd -P)"
mkdir -p output/figures
cp docs/manuscript/assets/catalog-workflow.png output/figures/

template_checkout="$(mktemp -d)/template"
git clone https://github.com/docxology/template.git "$template_checkout"
git -C "$template_checkout" checkout --detach 87704feae0a4490ef7dad9c931d268e8c30273c2
cd "$template_checkout"
uv sync --locked
mkdir -p projects/working
ln -s "$service_checkout" projects/working/service
uv run --no-sync python scripts/pipeline/stage_03_render.py --project working/service
uv run --no-sync python scripts/pipeline/stage_04_validate.py --project working/service
```

The renderer resolves the registered project's `docs/manuscript/` source
and reads figures staged in `output/figures/`. Inspect
`output/pdf/service_combined.pdf` and `output/reports/validation_report.md`
in the service checkout. The PDF should contain the catalog model, export
workflow and figure, sample verification, limitations, and bibliography.
