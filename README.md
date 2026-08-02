# rdkit

TAFFISH tool app for [RDKit](https://www.rdkit.org/), the open-source C++ and
Python toolkit for cheminformatics and molecular machine learning.

## Package Identity

- App name: `rdkit`
- Command: `taf-rdkit`
- TAFFISH version: `2026.03.5-r1`
- App kind: `tool`
- Container image: `ghcr.io/taffish/rdkit:2026.03.5-r1`
- Default command: `python`
- Python version: `3.12.13`
- Runtime source: conda-forge `main` label, `rdkit=2026.03.5`
- Upstream release: `Release_2026_03_5`
- Native platforms: `linux/amd64`, `linux/arm64`
- Upstream license: `BSD-3-Clause`
- TAFFISH wrapper license: `Apache-2.0`

## What This App Packages

RDKit is primarily a software library, not a single `rdkit` command-line
program. This app therefore exposes a pinned Python runtime instead of
inventing a partial replacement CLI.

The image includes:

- RDKit Python bindings and C++ shared runtime libraries
- molecule readers and writers for common RDKit-supported formats, including
  SMILES, SMARTS, SDF/Mol, PDB, and reaction formats
- molecular descriptors, fingerprints, similarity and substructure search
- chemical reactions, standardization, stereochemistry, conformer generation,
  force fields, 2D coordinates, 3D operations, and molecular drawing
- InChI, Avalon, CoordGen, FreeSASA, PandasTools, and other capabilities enabled
  by the conda-forge RDKit build
- RDKit runtime data and the upstream `Contrib` files; SA_Score is verified
- NumPy, pandas, matplotlib, Pillow, Cairo, ReportLab, and SQLAlchemy dependencies
- `rdkit-runtime-info`, a small TAFFISH helper for version and capability probes
- upstream README, release notes, license, conda package inventory, and explicit
  package manifest under `/opt/rdkit/share`

The selected conda-forge `main`-label RDKit package is pinned independently per
platform:

| Platform | Package build | Package SHA256 |
| --- | --- | --- |
| `linux/amd64` | `py312hc61c88d_0` | `abcc0d709514bcc73309ed86ae528d3d8d4a429bd9ce1e740e68dc4d3f7b9fc9` |
| `linux/arm64` | `py312h6765812_0` | `9bbb6df015de6ddd5b328949e514fcc716bcf158d554cc5e69746117ed7ae47e` |

## Scope

Supported through the upstream Python API:

- molecule parsing, sanitization, conversion, and serialization
- SMARTS matching, substructure searching, and molecular transformations
- descriptor and fingerprint generation for classical analysis and ML features
- similarity calculations, diversity selection, and clustering primitives
- reaction parsing, execution, and product enumeration
- tautomer, charge, salt, fragment, and molecular standardization utilities
- 2D and 3D coordinate generation, conformer embedding, force-field optimization,
  shape operations, and molecular depiction
- InChI/InChIKey, Avalon fingerprints, FreeSASA, and the SA_Score Contrib module
- data-frame integration and image/report output available through packaged
  Python dependencies

This app intentionally does not include:

- the RDKit PostgreSQL cartridge or a PostgreSQL server
- C++ development headers, static libraries, compilers, or build tools
- Java, C#, JavaScript, CFFI, KNIME, or native GUI distributions
- Jupyter Notebook/Lab or another long-running interactive service
- optional dependencies used only by selected Contrib scripts, such as SciPy,
  scikit-learn, seaborn, IPython, requests, CACTVS, or `bayon`
- project-specific compound collections, trained ML models, or remote databases

These are separate upstream distributions or development/service concerns, not
hidden requirements of ordinary RDKit Python scripts. The shared C++ runtime
libraries required by the Python bindings are included. The upstream `Contrib`
tree is retained for reference and supported modules, but it is not a single
dependency-closed API; only SA_Score is explicitly exercised by this app's smoke.

## Usage

Print the RDKit version and packaged capability summary:

```bash
taf-rdkit rdkit-runtime-info
```

Run a project Python script explicitly:

```bash
taf-rdkit python analysis.py
```

Inspect packaged versions and capabilities:

```bash
taf-rdkit rdkit-runtime-info
taf-rdkit rdkit-runtime-info --json
```

Use an upstream module CLI, such as SDF-to-CSV conversion:

```bash
taf-rdkit python -m rdkit.Chem.ChemUtils.SDFToCSV molecules.sdf molecules.csv
```

Minimal script example:

```python
from rdkit import Chem, DataStructs
from rdkit.Chem import Descriptors, rdFingerprintGenerator

aspirin = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")
caffeine = Chem.MolFromSmiles("Cn1c(=O)c2c(ncn2C)n(C)c1=O")

generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
similarity = DataStructs.TanimotoSimilarity(
    generator.GetFingerprint(aspirin),
    generator.GetFingerprint(caffeine),
)

print(Chem.MolToSmiles(aspirin))
print(Descriptors.MolWt(aspirin))
print(similarity)
```

Save that code as `analysis.py`, then run:

```bash
taf-rdkit python analysis.py
```

## Command Mode

The app uses the standard thin TAFFISH wrapper:

```taf
<taf-app:container:ghcr.io/taffish/rdkit:2026.03.5-r1>
python ::*ARGV*::
```

Option-leading arguments use the default Python command. A non-option-leading
argument activates TAFFISH command mode and is interpreted as an executable
inside the container.

Because TAFFISH command payloads are shell-native, do not rely on an inline
`python -c` argument containing spaces, quotes, semicolons, or other shell
syntax. Put non-trivial Python in a version-controlled script instead. This also
makes the analysis auditable and avoids host-shell quoting differences.

For that reason, use:

```bash
taf-rdkit python analysis.py
```

Do not use `taf-rdkit analysis.py`; a normal `.py` file is not itself a
container executable. The explicit form also makes provenance easier to read.

Wrapper and upstream help are different:

```bash
taf-rdkit --help
taf-rdkit -- --help
taf-rdkit python --help
```

The first command shows this app's terminal manual. The latter two access the
default Python runtime help.

## Inputs And Outputs

RDKit inputs and outputs are controlled by the user's Python code. Common inputs
include SMILES/SMARTS text, SDF/Mol files, PDB files, reaction files, and tabular
compound metadata. Common outputs include canonical SMILES, SDF/Mol files,
fingerprint arrays, descriptor tables, transformed molecules, conformer files,
and SVG/PNG/PDF molecular depictions.

TAFFISH mounts the current working directory according to the selected backend.
Use paths visible inside that mounted working directory and choose output names
explicitly in the Python script. RDKit itself does not impose a single output
directory or overwrite policy.

## Runtime Data And External Resources

Core RDKit runtime data and Contrib files are bundled under
`/opt/rdkit/share/RDKit`. Ordinary molecule parsing, descriptors, fingerprints,
standardization, coordinate generation, depiction, and file conversion work
offline and require no external database.

Selected optional Contrib scripts declare extra Python packages or external
programs that are not dependencies of the standard RDKit runtime. Use a derived
environment or a separate purpose-built app when one of those scripts is needed.

Project compound libraries, proprietary structures, trained models, PostgreSQL
databases, and remote chemistry services are not bundled. Supply such resources
as ordinary input files or connect to them explicitly from project code. The app
does not download data or contact remote services during startup or smoke tests.

## Platform And Resources

The image has native `linux/amd64` and `linux/arm64` builds. Conda-forge provides
separate RDKit `2026.03.5` packages for both platforms, and index smoke runs
the same API, drawing, 3D, SA_Score, and file-conversion paths on each build.

Small molecule operations are lightweight. Large collections, fingerprint
matrices, conformer ensembles, 3D optimization, or pandas data frames can require
substantial memory and CPU. Threading and process-level parallelism are controlled
by the user's Python code and the numerical libraries in the environment.

Interactive Python sessions require an interactive backend invocation. For
reproducible analyses, prefer version-controlled Python scripts.

## Image Construction And Size

The image uses conda-forge because RDKit upstream recommends conda and the exact
`2026.03.5` release is available from its stable `main` label as separate,
checksum-pinned packages for both Linux architectures. Keeping one distribution
source also preserves the validated dependency and runtime-data layout across
updates.

A multi-stage build keeps micromamba caches and downloaded package archives out
of the final image. The final runtime removes development headers, CMake metadata,
pkg-config files, static libraries, dependency test suites, Conda solver metadata,
bytecode caches, third-party development documentation, and manual-page build
artifacts. It retains runtime libraries, data, Contrib, fonts, Python modules,
upstream RDKit documentation, and license notices. Exact installed package
manifests remain available for audit.

## Testing

Together, the lightweight build-time checks and independent index smoke cover:

- Python `3.12.13` and RDKit runtime version `2026.03.5`
- imports across the major RDKit Python package families
- InChI, Avalon, CoordGen, FreeSASA, PandasTools, Cairo drawing, and SA_Score
- SMILES and SMARTS parsing, canonicalization, descriptors, substructure matching,
  Morgan fingerprints, Tanimoto similarity, and chemical reactions
- salt/fragment standardization, conformer embedding, UFF optimization, and SASA
- the `ROMol.SetName()` / `ROMol.GetName()` accessors added in `2026.03.5`
- SDF write/read round trip, SVG and PNG depiction, pandas SDF loading, and the
  upstream `SDFToCSV` module CLI
- dynamic-library resolution for the Python executable, RDKit shared libraries,
  and RDKit extension modules

Every index smoke command is self-contained and runs without network access. The
smoke does not replace scientific validation of a production compound library,
model, force-field protocol, stereochemical policy, or PostgreSQL deployment.

## Troubleshooting

- If `taf-rdkit analysis.py` reports that `analysis.py` is not executable, use
  `taf-rdkit python analysis.py`.
- If an interactive Python prompt immediately exits, enable stdin/TTY support in
  the selected Docker, Podman, or Apptainer invocation, or run a script instead.
- If a path is missing, confirm it is inside a directory mounted and visible to
  the selected container backend.
- If a project imports Jupyter, PostgreSQL cartridge, Java/.NET, or C++ headers,
  install or package that separate environment; those surfaces are outside this
  runtime app.
- If an optional Contrib script reports a missing package or executable, consult
  that script's upstream README and use a derived environment; only SA_Score is
  part of the app's verified Contrib surface.

## License And Citation

The TAFFISH packaging code and documentation are distributed under
`Apache-2.0`.

Upstream RDKit is distributed under `BSD-3-Clause`. Its license is preserved at
`/opt/rdkit/share/licenses/rdkit/license.txt`. Conda dependency license material
under `/opt/rdkit/share/licenses` remains part of the runtime image.

RDKit states that it has no single official publication and recommends citing:

> RDKit: Open-source cheminformatics. <https://www.rdkit.org>

Include the relevant version DOI when appropriate. The RDKit Zenodo concept DOI
is <https://doi.org/10.5281/zenodo.591637>.

## Upstream Resources

- RDKit homepage: <https://www.rdkit.org/>
- GitHub repository: <https://github.com/rdkit/rdkit>
- `2026.03.5` release: <https://github.com/rdkit/rdkit/releases/tag/Release_2026_03_5>
- Installation guide: <https://www.rdkit.org/docs/Install.html>
- Getting started in Python: <https://www.rdkit.org/docs/GettingStartedInPython.html>
- RDKit Book: <https://www.rdkit.org/docs/RDKit_Book.html>
- Python API reference: <https://www.rdkit.org/docs/api-docs.html>
- Cookbook: <https://www.rdkit.org/docs/Cookbook.html>
