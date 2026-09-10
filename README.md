# rdkit

`rdkit` packages [RDKit](https://www.rdkit.org/) for TAFFISH.

Package identity:

- name / command / kind: `rdkit` / `taf-rdkit` / `tool`
- version: `2026.03.6-r1`; Python `3.12.13`
- image: `ghcr.io/taffish/rdkit:2026.03.6-r1`
- native platforms: `linux/amd64`, `linux/arm64`
- upstream: [Release_2026_03_6](https://github.com/rdkit/rdkit/releases/tag/Release_2026_03_6),
  commit `0e0d85f4ca34aeae15dfc0f7cf5503bdb0a8e985`
- packaging license: Apache-2.0; upstream license: BSD-3-Clause

## What This App Packages

RDKit is primarily a C++/Python library, not a single `rdkit` CLI. This app
provides its Python runtime and required shared libraries, without inventing a
replacement analysis interface. The default command remains `python`.

Stable conda-forge `main` packages are independently fixed and SHA256-checked;
base OCI manifests are digest-pinned in the Dockerfile.

| Platform | Component/build | SHA256 |
| --- | --- | --- |
| amd64 | rdkit `py312h5eb2359_0` | `0704fd0109b30020c37077d4318dce3db1ded221354d1d0353cb9903c71aba83` |
| arm64 | rdkit `py312h1a38de7_0` | `72e3601ba0c2816be0b089ee5fb02366256bd9038c92bc7bba7a2d1a4cfa4b51` |
| amd64 | librdkit `h61648e3_0` | `d7f25848599806a17e04b9863d47c1a7e1866f5da23cd028c7a1d7cdb77c1d05` |
| arm64 | librdkit `h4ab84a9_0` | `4bdfbaa39f445b9926987cf32798a3b35f55e879a5d34b91cf24bcba06e227f7` |

## Scope

Supported through upstream Python APIs:

- structure I/O, SMILES/SMARTS, substructure matching and descriptors
- fingerprints, similarity, reaction execution and molecular standardization
- stereochemistry, 2D coordinates, 3D conformers, force fields and shape operations
- InChI/InChIKey, Avalon, CoordGen, FreeSASA and PandasTools SDF integration
- headless SVG/PNG drawing; PDF reports by composing images with ReportLab
- Synthon space APIs, including the 2026.03.6 shape-search addition
- bundled SA_Score and NP_Score models and scoring code

The upstream Contrib tree is retained, but is not dependency-closed. Presence of
a script or a successful import probe is not proof of all its functionality.
This app does not supply a GUI, notebook, PostgreSQL cartridge/server, C++ SDK,
alternate-language distribution or every optional Contrib dependency.

## Container Contents

- `python`, `python3`: Python with RDKit bindings and runtime shared libraries
- `rdkit-runtime-info`: versions and import/file availability probes
- NumPy, pandas, matplotlib, Pillow, Cairo, ReportLab and SQLAlchemy
- `/opt/rdkit/share/RDKit`: data, fonts, feature definitions and Contrib
- `/opt/rdkit/share/doc/rdkit`: source identity, upstream README/release notes,
  `conda-packages.txt` and `conda-explicit.txt`
- `/opt/rdkit/share/licenses/rdkit/license.txt`: upstream BSD notice
- `/opt/rdkit/share/licenses/conda`: per-package dependency notices and a
  name/version/build/source/checksum inventory, verified during build and smoke

## Usage

After this release is published and indexed, install with
`taf install rdkit 2026.03.6-r1`. Commands below use the installed `taf-rdkit` alias.

Save as `analysis.py` in the working directory:

```python
import os
import sys
from rdkit import Chem, RDConfig
from rdkit.Chem import Descriptors, Draw
sys.path.insert(0, os.path.join(RDConfig.RDContribDir, "SA_Score"))
sys.path.insert(0, os.path.join(RDConfig.RDContribDir, "NP_Score"))
import sascorer
import npscorer

mol = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")
assert mol is not None
model = npscorer.readNPModel()  # load the bundled model once per process
print(Chem.MolToSmiles(mol), Descriptors.MolWt(mol))
print(sascorer.calculateScore(mol), npscorer.scoreMol(mol, model))
Draw.MolToFile(mol, "molecule.svg")
Draw.MolToFile(mol, "molecule.png")
```

Conda installs Contrib under `RDConfig.RDContribDir`, not `rdkit.Contrib`.

```sh
taf-rdkit python analysis.py
taf-rdkit python -m rdkit.Chem.ChemUtils.SDFToCSV input.sdf output.csv
taf-rdkit rdkit-runtime-info --json
taf-rdkit -- --help
```

For PDF, add after creating the PNG (MolToFile itself accepts PNG/SVG, not PDF):

```python
from reportlab.pdfgen import canvas
report = canvas.Canvas("molecule.pdf")
report.drawImage("molecule.png", 40, 500, width=420, height=260)
report.save()
```

## Backend Usage and Capability Matrix

```sh
TAFFISH_CONTAINER_BACKEND=docker taf-rdkit python analysis.py
TAFFISH_CONTAINER_BACKEND=podman taf-rdkit python analysis.py
TAFFISH_CONTAINER_BACKEND=apptainer taf-rdkit python analysis.py
```

| Capability | Docker | Podman | Apptainer | Boundary |
| --- | --- | --- | --- | --- |
| CPU scripts, drawing, bundled models | supported | supported | supported | Native Linux image; Apptainer needs Linux |
| External read-only inputs | `-v HOST:/inputs:ro` | `-v HOST:/inputs:ro` | `--bind HOST:/inputs:ro` | Optional site policy, not automatic discovery |
| GUI/Notebook/KNIME/PyMol | unsupported | unsupported | unsupported | Separate GUI integration; use host SVG/PNG viewing |
| GPU | N/A | N/A | N/A | No GPU execution surface in this runtime |

No app-specific device, network, port or emulation flags are needed. Replace the
host path below with an existing readable directory, read `/inputs` in the
script, and write results to the mounted working directory:

```sh
TAFFISH_CONTAINER_BACKEND=docker TAFFISH_DOCKER_RUN_ARGS='-v /srv/chemistry/library:/inputs:ro' taf-rdkit python analysis.py
TAFFISH_CONTAINER_BACKEND=podman TAFFISH_PODMAN_RUN_ARGS='-v /srv/chemistry/library:/inputs:ro' taf-rdkit python analysis.py
TAFFISH_CONTAINER_BACKEND=apptainer TAFFISH_APPTAINER_RUN_ARGS='--bind /srv/chemistry/library:/inputs:ro' taf-rdkit python analysis.py
```

Never write into `/opt/rdkit`: it is immutable in SIFs. Temporary files belong in
a unique `/tmp` or workdir directory. Engines may need an initial image pull;
the analysis examples themselves are offline.

## Command Mode

The standard thin entry defaults to `python ::*ARGV*::`. Non-option-leading
arguments select an executable: use `taf-rdkit python analysis.py`, not
`taf-rdkit analysis.py`. Keep non-trivial code in files instead of shell-rich
inline `python -c` strings. Quote space-containing paths for both the host shell
and the shell-native command payload, for example `taf-rdkit python "'my script.py'"`.

`--version` shows the app version; `-- --version` shows Python;
`rdkit-runtime-info --version` shows RDKit. `--help` is wrapper help, while
`-- --help` or `python --help` is Python help.

## Inputs and Output Notes

Inputs are scripts, structures and compound tables. Synthon spaces are
user-selected project libraries, not a canonical database downloaded by RDKit.
Outputs, overwrite policy and conformer/thread limits are chosen by the script.
Check invalid SDF records (`None`). Large libraries, conformer ensembles and
fingerprint matrices can exhaust RAM/storage; no scientific thresholds are imposed.

### Read-only Synthon binary libraries

Upstream 2026.03.6 opens `.spc` files with `O_RDWR` in its Linux memory-mapped
reader, even though the mapping is read-only. Direct `ReadDBFile()` on a read-only
bind or a non-writable shared file is therefore unsupported. This is a file-access
limitation, not an algorithm change, and TAFFISH does not patch it. Keep the master
read-only and use a private writable copy; allow enough scratch for the entire file.
For a mounted `/inputs/library.spc`, put this in your script:

```python
import pathlib
import shutil
import tempfile
from rdkit.Chem import rdSynthonSpaceSearch
with tempfile.TemporaryDirectory(prefix="rdkit-space-") as tmp:
    local = pathlib.Path(tmp) / "library.spc"
    shutil.copyfile("/inputs/library.spc", local)
    space = rdSynthonSpaceSearch.SynthonSpace()
    space.ReadDBFile(str(local))
    print(space.GetNumProducts())
    # Run your searches here, before the private copy is removed.
```

Use the same three backend commands and read-only binds above. `ReadTextFile`
and ordinary SDF inputs do not need this workaround. Do not chmod the shared
master, remove the `:ro` bind, or add write permissions for other users.

## Resources, Databases, and Platform

| Resource unit | Source/reuse | Installation and discovery |
| --- | --- | --- |
| Core data, fonts, feature definitions | Fixed package contents | Bundled read-only under RDBASE |
| SA `fpscores.pkl.gz` | Small fixed upstream model | Bundled; scorer discovers sibling file |
| NP `publicnp.model.gz` | Small fixed upstream model | Bundled; `readNPModel()` uses sibling file |
| Compound/Synthon libraries, trained project models | User inputs, user-controlled license/identity | Explicit paths and three-backend read-only bind above |
| PostgreSQL and remote-service integrations | Separate server/distribution/credentials | Unsupported here; purpose-built environment |

SA SHA256: `10dcef9340c873e7b987924461b0af5365eb8dd96be607203debe8ddf80c1e73`.
NP SHA256: `34db5b02d762e05a0243e640aee24202a5303b7ec810ced7ff929a233e082ab6`.
Both are bound to the verified package and tested offline. Upstream code/notices
remain in their Contrib directories; see the SA 2009 J. Cheminformatics and NP
2008 JCIM references in their READMEs.

No separate downloader, per-user copy, writable model root, override/disable
environment variable or root initialization is needed. Once an image is in a
site-managed readable OCI/SIF store, ordinary users can reuse the same immutable
data. Engine/socket or SIF access is a site decision; this app changes no host
permissions. Opt out by not calling the scorer. Upstream explicit model-file
parameters can load trusted replacements, which are not covered by the bundled
model tests. **Untrusted pickle/model files can execute Python code.**

## Boundaries and Optional GUI Review

Current source and official companions were reviewed, not only Conda dependencies.
This remains an explicitly **headless Python runtime**:

| Surface | Reason not exposed here | Alternative |
| --- | --- | --- |
| `Draw.ShowMol`, Qt painter, PyMol bridge | Requires Tk/Qt desktop or external PyMol XML-RPC process | Save SVG/PNG or use a dedicated desktop |
| `IPythonConsole`, `InteractiveRenderer`, py3Dmol | Needs notebook/browser; interactive renderer loads external CDN JavaScript | Separate authenticated notebook with pinned assets |
| Official KNIME nodes | Plugins for a separately installed KNIME Analytics Platform | [KNIME integration](https://github.com/rdkit/knime-rdkit) |
| Official JS renderer | Separate JavaScript/WebAssembly browser package | [Structure renderer](https://github.com/rdkit/rdkit-structure-renderer) |
| PostgreSQL cartridge, other language wrappers, C++ SDK | Separate server/build interfaces; cartridge recipe excludes aarch64 | Purpose-built server/development app |
| Other Contrib/legacy bridges | May need SciPy, scikit-learn, seaborn, IPython, requests, xlsxwriter, CACTVS or bayon | Dependency-closed environment for the chosen script |

No desktop/service launcher, listening port or notebook entry is exposed. This
is not a claim of complete upstream integration coverage. GUI lifecycle/menu
and GPU tests are N/A to the public headless surface; static drawing is tested.

## Image Construction and Size

Multi-stage construction excludes micromamba/package caches. Headers, static
libraries, CMake/pkg-config metadata, solver metadata, dependency test suites and
bytecode are removed; runtime libraries, data, fonts, Contrib and notices remain.
Before package-cache cleanup, the build archives each installed Conda package's
`info/licenses` and installed/vendored notice files. Dependency documentation is
retained instead of deleting its whole tree. Offline checks verify every archived
notice's size and SHA256; packages without payload are identified separately.
Split FreeType notices are traced to the matching installed provider; GCC runtime
exceptions and the GPL-3 text, and SQLite's original header dedication, are retained.
RDKit/library/Python identities are fixed; other Conda dependencies are resolved
and recorded in the explicit manifest. Later builds are not claimed byte-identical.

## Troubleshooting

- Missing script: use explicit `python` and a mounted workdir path.
- Missing input: verify host permissions and a real backend bind, not a marker.
- Write failure under `/opt`: use workdir or a writable `/tmp`.
- Missing GUI/optional module: consult the boundary table and prepare a separate
  environment; do not install into the immutable running image.
- Unexpected chemistry: independently validate parsing, stereochemistry,
  standardization, force-field settings and model applicability.

## Testing

Build-time checks are lightweight: versions, ordinary help, imports, ROMol name
accessors (introduced in 2026.03.5) and dynamic-library resolution. Full 3D,
drawing and scoring stay in offline runtime smoke, not Docker build layers.

Independent manifest commands cover identity/help and a minimal real path:
parsing, SMARTS, descriptors, Morgan/Avalon fingerprints, reactions,
standardization, conformers/UFF/FreeSASA, InChI, SDF/pandas/CSV, SVG/PNG/PDF,
SA/NP scores, RDKit fingerprint `ignoreAtoms`, and tiny Synthon shape database
build/reload/search. Fresh scratch is owned by each command; existing output
directories are not overwritten.

Current-release native-platform, backend, read-only-root, real SIF and actual
wrapper-bind results are recorded in `release.md`. Smoke checks integration,
not full scientific validity on production chemistry datasets.

## License and Citation

Packaging: Apache-2.0. Upstream: BSD-3-Clause. Dependencies retain their own
notices, including the per-package Conda archive, Python distributions and Contrib. Cite
“RDKit: Open-source cheminformatics” with the version and
[upstream site](https://www.rdkit.org/); concept DOI:
[10.5281/zenodo.591637](https://doi.org/10.5281/zenodo.591637).

Further help: [Getting started](https://www.rdkit.org/docs/GettingStartedInPython.html),
[API](https://www.rdkit.org/docs/api-docs.html), [Book](https://www.rdkit.org/docs/RDKit_Book.html).
