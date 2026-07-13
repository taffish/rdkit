#!/opt/rdkit/bin/python
import os
import pathlib
import shutil
import sys

import pandas
import rdkit
from rdkit import Chem, DataStructs
from rdkit.Avalon import pyAvalonTools
from rdkit.Chem import AllChem, Descriptors, PandasTools, inchi, rdFreeSASA
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit.Chem import rdFingerprintGenerator


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main(output_dir):
    outdir = pathlib.Path(output_dir)
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True)

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
    sasa = rdFreeSASA.CalcSASA(ethanol_3d, [1.5] * ethanol_3d.GetNumAtoms())
    require(sasa > 0.0, "FreeSASA calculation failed")

    inchi_text = inchi.MolToInchi(aspirin)
    inchi_key = inchi.MolToInchiKey(aspirin)
    require(inchi_text.startswith("InChI=1S/"), "InChI generation failed")
    require(len(inchi_key) == 27, "InChIKey generation failed")

    sdf_path = outdir / "molecules.sdf"
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

    contrib = pathlib.Path(os.environ.get("RDBASE", "/opt/rdkit/share/RDKit")) / "Contrib" / "SA_Score"
    require((contrib / "sascorer.py").is_file(), "SA_Score Contrib files are missing")
    sys.path.insert(0, str(contrib))
    import sascorer

    sa_score = sascorer.calculateScore(aspirin)
    require(1.0 <= sa_score <= 10.0, "SA score is outside its expected range")

    summary = outdir / "summary.tsv"
    summary.write_text(
        "metric\tvalue\n"
        f"rdkit_version\t{rdkit.__version__}\n"
        f"molecule_count\t{len(molecules)}\n"
        f"fingerprint_similarity\t{similarity:.6f}\n"
        f"inchi_key\t{inchi_key}\n"
        f"sasa\t{sasa:.6f}\n"
        f"sa_score\t{sa_score:.6f}\n",
        encoding="utf-8",
    )
    require(summary.stat().st_size > 0, "summary output is empty")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: rdkit-smoke.py OUTDIR")
    main(sys.argv[1])
