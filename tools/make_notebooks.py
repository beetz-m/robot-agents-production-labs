#!/usr/bin/env python3
"""Build notebooks/labNN_*.ipynb from labs/labNN_*.py (the scripts stay the source of truth).

    python3 tools/make_notebooks.py            # needs nbformat
    python3 tools/make_notebooks.py --execute  # also runs every notebook (needs nbclient, ipykernel)

A notebook = title and docstring (markdown) + a prediction prompt + a setup cell + the lab's code (split at '# %%'
lines) + its '# Q:' lines as questions.
"""
import ast
import sys
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parent.parent
SETUP = "import sys\nsys.path[:0] = ['../labs', '..']   # the lab helpers and the tmodel package"


def build(py: Path):
    src = py.read_text()
    doc = ast.get_docstring(ast.parse(src)) or ""
    body = src.split('"""', 2)[2] if src.lstrip().startswith('"""') else src
    lines = body.splitlines()
    qs = [ln[5:] for ln in lines if ln.startswith("# Q: ")]
    code = "\n".join(ln for ln in lines if not ln.startswith("# Q: ")).strip("\n")
    chunks = [c.strip("\n") for c in code.split("\n# %%")]
    nb = nbf.v4.new_notebook()
    title = py.stem.replace("_", " ")
    nb.cells.append(nbf.v4.new_markdown_cell(f"# {title}\n\n{doc}\n\n*Teaching model of the textbook \"Robot Agents in "
                                             "Production\". Every parameter is ILLUSTRATIVE (see `../register.yaml`).*"))
    nb.cells.append(nbf.v4.new_markdown_cell("**Before you run anything:** write down what you expect, in numbers where you "
                                             "can. Compare afterwards, and keep the prediction even if it was wrong."))
    nb.cells.append(nbf.v4.new_code_cell(SETUP))
    for c in chunks:
        if c:
            nb.cells.append(nbf.v4.new_code_cell(c))
    if qs:
        nb.cells.append(nbf.v4.new_markdown_cell("## Questions\n\n" + "\n".join(f"{i + 1}. {q}" for i, q in enumerate(qs))))
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    return nb


def main():
    out = ROOT / "notebooks"
    out.mkdir(exist_ok=True)
    paths = []
    for py in sorted((ROOT / "labs").glob("lab[0-9]*.py")):
        p = out / (py.stem + ".ipynb")
        nbf.write(build(py), p)
        paths.append(p)
        print("wrote", p.relative_to(ROOT))
    if "--execute" in sys.argv:
        from nbclient import NotebookClient
        kernel = sys.argv[sys.argv.index("--kernel") + 1] if "--kernel" in sys.argv else "python3"
        for p in paths:
            nb = nbf.read(p, as_version=4)
            NotebookClient(nb, timeout=1800, kernel_name=kernel, resources={"metadata": {"path": str(out)}}).execute()
            print("executed", p.name)


if __name__ == "__main__":
    main()
