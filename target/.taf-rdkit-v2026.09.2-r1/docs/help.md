rdkit 2026.09.2-r1

Purpose:
  Run Python scripts for molecular structures, descriptors, fingerprints,
  reactions, 3D conformers and headless molecular drawing.

Usage:
  taf-rdkit python analysis.py
  taf-rdkit python -m rdkit.Chem.ChemUtils.SDFToCSV input.sdf output.csv
  taf-rdkit rdkit-runtime-info --json

Required inputs:
  Put analysis.py and its SMILES/SDF/Mol/PDB or table inputs in your working
  directory. Select output paths in your script and avoid existing filenames.
  Use explicit python: taf-rdkit analysis.py treats analysis.py as an executable.
  Keep non-trivial Python in a file, not a shell-rich inline python -c string.
  Space-containing path: taf-rdkit python "'my script.py'"

Common options:
  taf-rdkit python --help
  taf-rdkit python -m rdkit.Chem.ChemUtils.SDFToCSV --help
  taf-rdkit -- --version    Show Python version, not RDKit version.
  taf-rdkit rdkit-runtime-info --version

Key outputs:
  Scripts choose structure files, descriptor tables, fingerprints and images.
  Draw.MolToFile(mol, "molecule.svg") or "molecule.png" writes a depiction.
  For PDF, embed the PNG using ReportLab; MolToFile does not accept PDF.
  Invalid SDF records may return None: check records before further analysis.

Backend-specific use:
  Headless CPU scripts; no GPU, display server or port forwarding is required.
  Docker:    TAFFISH_CONTAINER_BACKEND=docker taf-rdkit python analysis.py
  Podman:    TAFFISH_CONTAINER_BACKEND=podman taf-rdkit python analysis.py
  Apptainer: TAFFISH_CONTAINER_BACKEND=apptainer taf-rdkit python analysis.py
  Use a native Linux amd64/arm64 image; Apptainer itself needs Linux.

Read-only inputs outside the working directory:
  Replace /srv/chemistry/library with your readable host directory; let your
  script read /inputs and write results to the current working directory.
  Docker:
    TAFFISH_CONTAINER_BACKEND=docker \
    TAFFISH_DOCKER_RUN_ARGS='-v /srv/chemistry/library:/inputs:ro' \
    taf-rdkit python analysis.py
  Podman:
    TAFFISH_CONTAINER_BACKEND=podman \
    TAFFISH_PODMAN_RUN_ARGS='-v /srv/chemistry/library:/inputs:ro' \
    taf-rdkit python analysis.py
  Apptainer:
    TAFFISH_CONTAINER_BACKEND=apptainer \
    TAFFISH_APPTAINER_RUN_ARGS='--bind /srv/chemistry/library:/inputs:ro' \
    taf-rdkit python analysis.py

Bundled scoring models:
  In analysis.py, use the packaged Contrib path (not rdkit.Contrib):
    import os, sys
    from rdkit import RDConfig
    sys.path.insert(0, os.path.join(RDConfig.RDContribDir, "SA_Score"))
    sys.path.insert(0, os.path.join(RDConfig.RDContribDir, "NP_Score"))
    import sascorer, npscorer
  Use sascorer.calculateScore(mol), or load npscorer.readNPModel() once and call
  npscorer.scoreMol(mol, model). Both models are bundled and read-only; no
  per-user/root download, model mount or internet access is needed.
  Never load an untrusted pickle/model file; it can execute Python code.

Synthon binary inputs:
  Linux ReadDBFile(.spc) requests write access in this upstream version.
  On all three backends, keep shared inputs read-only and copy the .spc to a
  private writable /tmp/workdir before loading; allow space for the full copy.
  See the README recipe. Do not chmod or make the shared master writable.

Immediate notes:
  GUI/Notebook/KNIME/PyMol integration is unsupported in this headless app on
  Docker, Podman and Apptainer: use a separately configured upstream GUI or
  save SVG/PNG for viewing on the host. Do not call Draw.ShowMol here.
  Other Contrib scripts may require extra packages or external programs;
  use the README scope table before choosing them.
  Large libraries and conformer ensembles can exhaust RAM or storage. Set
  thread/conformer limits in your code; write temporary data to /tmp or workdir.

More help:
  https://github.com/taffish/rdkit
  https://www.rdkit.org/docs/GettingStartedInPython.html

Wrapper options:
  taf-rdkit --help       Show this TAFFISH help.
  taf-rdkit --version    Show the app wrapper version.
  taf-rdkit --compile    Print the generated wrapper shell.
  taf-rdkit -- --help    Show default Python help.
