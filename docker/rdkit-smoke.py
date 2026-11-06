#!/opt/rdkit/bin/python
import os
import pathlib
import hashlib
import io
import math
import subprocess
import sys

import numpy
import pandas
import rdkit
from rdkit import Chem, DataStructs
from rdkit.Avalon import pyAvalonTools
from rdkit.Chem import AllChem, Descriptors, PandasTools, inchi, rdFreeSASA
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit.Chem import rdFingerprintGenerator, rdMolDescriptors
from rdkit.Chem import rdSynthonSpaceSearch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main(output_dir):
    outdir = pathlib.Path(output_dir)
    # A caller-owned output is never overwritten, even when it is a symlink.
    outdir.mkdir(parents=True, exist_ok=False)
    require(rdkit.__version__ == "2026.09.2", "wrong RDKit runtime")
    print("stage=conda-notices", flush=True)
    subprocess.run([sys.executable, "/opt/rdkit/share/testdata/conda-licenses.py", "verify"],
                   check=True)
    subprocess.run(["sha256sum", "-c", "SHA256SUMS"],
                   cwd="/opt/rdkit/share/licenses/rdkit/embedded", check=True)
    subprocess.run([sys.executable, "/opt/rdkit/share/testdata/prepare-sources.py", "verify",
                    "/opt/rdkit/share/licenses/rdkit/source"], check=True)
    print("stage=core", flush=True)

    records = [
        ("aspirin", "CC(=O)Oc1ccccc1C(=O)O"),
        ("caffeine", "Cn1c(=O)c2c(ncn2C)n(C)c1=O"),
        ("ethanol", "CCO"),
    ]
    molecules = []
    for name, smiles in records:
        mol = Chem.MolFromSmiles(smiles)
        require(mol is not None, f"failed to parse {name}")
        mol.SetProp("Name", name)
        molecules.append(mol)

    aspirin, caffeine, ethanol = molecules
    aspirin.SetName("aspirin")
    require(aspirin.GetName() == "aspirin", "ROMol name accessors failed")
    require(Chem.MolFromSmiles("C").GetName() == "", "unnamed ROMol returned a name")
    require(
        Chem.MolToSmiles(aspirin) == "CC(=O)Oc1ccccc1C(=O)O",
        "unexpected aspirin canonical SMILES",
    )
    require(aspirin.HasSubstructMatch(Chem.MolFromSmarts("c1ccccc1")), "substructure search failed")
    require(150.0 < Descriptors.MolWt(aspirin) < 200.0, "descriptor calculation failed")

    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    aspirin_fp = generator.GetFingerprint(aspirin)
    caffeine_fp = generator.GetFingerprint(caffeine)
    similarity = DataStructs.TanimotoSimilarity(aspirin_fp, caffeine_fp)
    require(0.0 < similarity < 1.0, "fingerprint similarity is outside the expected range")
    require(pyAvalonTools.GetAvalonFP(aspirin, nBits=512).GetNumBits() == 512, "Avalon failed")
    require(aspirin_fp.ToBitString() == DataStructs.BitVectToText(aspirin_fp),
            "2026.09.2 ToBitString binding failed")
    properties = rdMolDescriptors.Properties(['exactmw', 'tpsa', 'NumHBA'])
    reference = numpy.array([list(properties.ComputeProperties(mol)) for mol in molecules])
    for threads in (1, 2):
        batch = properties.ComputeProperties(molecules, numThreads=threads)
        require(batch.shape == (3, 3) and numpy.allclose(batch, reference),
                "2026.09.2 batch property calculation failed")
    ring_query = Chem.MolFromSmarts('*@{2}*')
    require(ring_query is not None and
            len(Chem.MolFromSmiles('c1ccc2ccccc2c1').GetSubstructMatches(ring_query)) == 1,
            "2026.09.2 SMARTS bond ring-count matching failed")

    # Retain the earlier ignoreAtoms regression alongside current-release checks.
    path_generator = rdFingerprintGenerator.GetRDKitFPGenerator(
        numBitsPerFeature=1, minPath=2, maxPath=3
    )
    chain = Chem.MolFromSmiles("CCCO")
    require(len(path_generator.GetSparseCountFingerprint(chain).GetNonzeroElements()) == 3,
            "RDKit fingerprint baseline failed")
    require(not path_generator.GetSparseCountFingerprint(chain, ignoreAtoms=[2]).GetNonzeroElements(),
            "ignoreAtoms regression")

    reaction = AllChem.ReactionFromSmarts("[C:1](=[O:2])O.[N:3]>>[C:1](=[O:2])[N:3]")
    products = reaction.RunReactants((Chem.MolFromSmiles("CC(=O)O"), Chem.MolFromSmiles("CN")))
    require(bool(products), "reaction execution produced no products")

    salt = Chem.MolFromSmiles("CC(=O)[O-].[Na+]")
    parent = rdMolStandardize.FragmentParent(salt)
    require(parent.GetNumAtoms() < salt.GetNumAtoms(), "molecule standardization did not remove the salt")

    ethanol_3d = Chem.AddHs(ethanol)
    require(
        AllChem.EmbedMolecule(ethanol_3d, randomSeed=0xC0FFEE) == 0,
        "3D conformer generation failed",
    )
    AllChem.UFFOptimizeMolecule(ethanol_3d, maxIters=50)
    require(ethanol_3d.GetNumConformers() == 1, "3D conformer is missing")
    # Preserve opt-in beta ETKDGv4 introduced in 2026.09.1; keep upstream defaults.
    from rdkit.Chem import rdDistGeom
    v4 = rdDistGeom.ETKDGv4()
    v4.randomSeed = 0xC0FFEE
    v4.numThreads = 1
    v4_mol = Chem.AddHs(Chem.MolFromSmiles("CCCC"))
    require(rdDistGeom.EmbedMolecule(v4_mol, v4) == 0,
            "opt-in ETKDGv4 tiny conformer failed")
    require(v4_mol.GetNumConformers() == 1, "ETKDGv4 conformer missing")
    # Preserve atom maps when canonical=False and ignoreAtomMapNumbers=True.
    mapped = Chem.MolFromSmiles("[CH3:7][OH:8]")
    text = Chem.MolToSmiles(mapped, canonical=False, ignoreAtomMapNumbers=True)
    require(":7" in text and ":8" in text, "noncanonical SMILES lost atom maps")
    sasa = rdFreeSASA.CalcSASA(ethanol_3d, [1.5] * ethanol_3d.GetNumAtoms())
    require(sasa > 0.0, "FreeSASA calculation failed")

    inchi_text = inchi.MolToInchi(aspirin)
    inchi_key = inchi.MolToInchiKey(aspirin)
    require(inchi_text.startswith("InChI=1S/"), "InChI generation failed")
    require(len(inchi_key) == 27, "InChIKey generation failed")

    sdf_path = outdir / "molecules.sdf"
    print("stage=io-and-drawing", flush=True)
    writer = Chem.SDWriter(str(sdf_path))
    for mol in molecules:
        writer.write(mol)
    writer.close()
    require(sdf_path.stat().st_size > 0, "SDF output is empty")
    reread = [mol for mol in Chem.SDMolSupplier(str(sdf_path)) if mol is not None]
    require(len(reread) == len(molecules), "SDF round trip lost molecules")

    frame = PandasTools.LoadSDF(str(sdf_path), idName="Name", molColName="ROMol")
    require(isinstance(frame, pandas.DataFrame) and len(frame) == 3, "PandasTools SDF load failed")

    svg_drawer = rdMolDraw2D.MolDraw2DSVG(420, 260)
    rdMolDraw2D.PrepareAndDrawMolecule(svg_drawer, aspirin, legend="aspirin")
    svg_drawer.FinishDrawing()
    svg = svg_drawer.GetDrawingText()
    require("<svg" in svg and len(svg) > 1000, "SVG depiction failed")
    (outdir / "molecule.svg").write_text(svg, encoding="utf-8")

    png_drawer = rdMolDraw2D.MolDraw2DCairo(420, 260)
    rdMolDraw2D.PrepareAndDrawMolecule(png_drawer, aspirin, legend="aspirin")
    png_drawer.FinishDrawing()
    png = png_drawer.GetDrawingText()
    require(png.startswith(b"\x89PNG") and len(png) > 1000, "PNG depiction failed")
    (outdir / "molecule.png").write_bytes(png)

    # MolToFile supports PNG/SVG, not PDF. Compose a PDF with packaged ReportLab.
    pdf_path = outdir / "molecule.pdf"
    pdf = canvas.Canvas(str(pdf_path), pagesize=(460, 300))
    pdf.drawImage(ImageReader(io.BytesIO(png)), 20, 20, width=420, height=260)
    pdf.save()
    require(pdf_path.read_bytes().startswith(b"%PDF-"), "ReportLab PDF output failed")

    print("stage=bundled-models", flush=True)
    contrib = pathlib.Path(os.environ.get("RDBASE", "/opt/rdkit/share/RDKit")) / "Contrib" / "SA_Score"
    require((contrib / "sascorer.py").is_file(), "SA_Score Contrib files are missing")
    require(hashlib.sha256((contrib / "fpscores.pkl.gz").read_bytes()).hexdigest()
            == "10dcef9340c873e7b987924461b0af5365eb8dd96be607203debe8ddf80c1e73",
            "bundled SA model identity mismatch")
    sys.path.insert(0, str(contrib))
    import sascorer

    sa_score = sascorer.calculateScore(aspirin)
    require(1.0 <= sa_score <= 10.0, "SA score is outside its expected range")

    np_contrib = contrib.parent / "NP_Score"
    require(hashlib.sha256((np_contrib / "publicnp.model.gz").read_bytes()).hexdigest()
            == "34db5b02d762e05a0243e640aee24202a5303b7ec810ced7ff929a233e082ab6",
            "bundled NP model identity mismatch")
    sys.path.insert(0, str(np_contrib))
    import npscorer

    np_result = npscorer.scoreMolWConfidence(aspirin, npscorer.readNPModel())
    require(math.isfinite(np_result.nplikeness) and 0 <= np_result.confidence <= 1,
            "NP model evaluation failed")

    print("stage=synthon-shapes", flush=True)
    # Four synthetic building blocks: no external compound library or download.
    space_path = outdir / "tiny-space.txt"
    space_path.write_text(
        "SMILES\tsynton_id\tsynton#\treaction_id\n"
        "CC(=O)[1*]\ta1\t0\tamide\n"
        "CCC(=O)[1*]\ta2\t0\tamide\n"
        "[1*]NC\tb1\t1\tamide\n"
        "[1*]NCC\tb2\t1\tamide\n", encoding="utf-8")
    space = rdSynthonSpaceSearch.SynthonSpace()
    space.ReadTextFile(str(space_path))
    build = rdSynthonSpaceSearch.ShapeBuildParams()
    build.numThreads = 1
    build.numConfs = 3
    space.BuildSynthonShapes(build)
    require(space.GetNumReactions() == 1 and space.GetNumProducts() == 4,
            "tiny synthon space inventory failed")
    space.WriteDBFile(str(outdir / "tiny-space.spc"))
    reloaded = rdSynthonSpaceSearch.SynthonSpace()
    reloaded.ReadDBFile(str(outdir / "tiny-space.spc"))
    query = Chem.AddHs(Chem.MolFromSmiles("CC(=O)NC"))
    require(AllChem.EmbedMolecule(query, randomSeed=0xDAC) == 0, "shape query embedding failed")
    query = Chem.RemoveHs(query)
    params = rdSynthonSpaceSearch.SynthonSpaceSearchParams()
    params.numThreads = 1
    params.numConformers = 3
    params.randomSeed = 0xDAC
    params.similarityCutoff = 0.1
    params.maxHits = 4
    hits = reloaded.ShapeSearch(query, params).GetHitMolecules()
    require(bool(hits), "2026.09.2 tiny synthon shape search returned no hits")

    summary = outdir / "summary.tsv"
    summary.write_text(
        "metric\tvalue\n"
        f"rdkit_version\t{rdkit.__version__}\n"
        "romol_name_accessor\tavailable\n"
        f"molecule_count\t{len(molecules)}\n"
        f"fingerprint_similarity\t{similarity:.6f}\n"
        f"inchi_key\t{inchi_key}\n"
        f"sasa\t{sasa:.6f}\n"
        f"sa_score\t{sa_score:.6f}\n",
        encoding="utf-8",
    )
    require(summary.stat().st_size > 0, "summary output is empty")
    print(f"PASS rdkit={rdkit.__version__} np_score={np_result.nplikeness:.6f} shape_hits={len(hits)}",
          flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: rdkit-smoke.py OUTDIR")
    main(sys.argv[1])
