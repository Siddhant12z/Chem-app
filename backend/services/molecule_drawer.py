"""
Molecule drawing module using RDKit for server-side molecule rendering.
This provides reliable molecule diagram generation without browser dependencies.
"""

import base64
import io
from typing import Optional, Tuple
import os
import json
import requests
from rdkit import Chem
from rdkit.Chem import Draw, rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D
from PIL import Image


# Curated name -> canonical SMILES map (extendable; initial core set)
CURATED_SMILES: dict[str, str] = {
    # Simple inorganics
    "water": "O",
    "ammonia": "N",
    "hydrogen peroxide": "OO",
    "carbon dioxide": "O=C=O",
    "carbon monoxide": "[C-]#[O+]",

    # Alkanes / alkenes / alkynes
    "methane": "C",
    "ethane": "CC",
    "propane": "CCC",
    "ethene": "C=C",
    "ethylene": "C=C",
    "acetylene": "C#C",

    # Alcohols and oxygenates
    "methanol": "CO",
    "ethanol": "CCO",
    "isopropanol": "CC(O)C",
    "phenol": "Oc1ccccc1",

    # Carbonyls / acids / esters
    "formaldehyde": "C=O",
    "acetaldehyde": "CC=O",
    "ethanal": "CC=O",
    "acetone": "CC(=O)C",
    "acetic acid": "CC(=O)O",
    "methyl acetate": "CC(=O)OC",

    # Aromatics
    "benzene": "c1ccccc1",
    "toluene": "Cc1ccccc1",

    # Mineral acids examples
    "nitric acid": "O[N+]([O-])=O",
    "sulfuric acid": "OS(=O)(=O)O",
}

# Merge extra curated list if available
def _load_extra_curated() -> dict[str, str]:
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        extra_path = os.path.join(here, "curated_smiles_extra.json")
        if os.path.exists(extra_path):
            with open(extra_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return {k.lower(): v for k, v in data.items() if isinstance(k, str) and isinstance(v, str)}
    except Exception as _:
        pass
    return {}

CURATED_SMILES.update(_load_extra_curated())


def _normalize_smiles(smiles: str) -> str | None:
    """Return RDKit-canonical SMILES or None if invalid."""
    if not smiles:
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            return None
        return Chem.MolToSmiles(mol)
    except Exception:
        return None


def resolve_curated_or_candidate(name: str | None, candidate_smiles: str | None) -> tuple[str | None, str]:
    """
    Resolve the most reliable SMILES for a (name, candidate) pair.

    Order of preference:
    1) Curated map by name (if present)
    2) RDKit-normalized candidate (if valid)

    Returns: (smiles, source) where source ∈ {"curated", "llm", "unknown"}
    """
    if name:
        key = name.strip().lower()
        curated = CURATED_SMILES.get(key)
        if curated:
            norm = _normalize_smiles(curated)
            if norm:
                return norm, "curated"

    norm_candidate = _normalize_smiles(candidate_smiles or "")
    if norm_candidate:
        return norm_candidate, "llm"

    # Try OPSIN resolver for long‑tail names
    if name:
        opsin = _resolve_with_opsin(name)
        if opsin:
            return opsin, "opsin"

    return None, "unknown"


def _resolve_with_opsin(name: str) -> str | None:
    """
    Resolve SMILES using OPSIN public service.
    API: https://opsin.ch.cam.ac.uk/opsin/{name}.json
    """
    try:
        url = f"https://opsin.ch.cam.ac.uk/opsin/{requests.utils.quote(name)}.json"
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            data = r.json()
            smiles = data.get("smiles") if isinstance(data, dict) else None
            norm = _normalize_smiles(smiles or "")
            if norm:
                # Cache in memory for this run
                CURATED_SMILES[name.strip().lower()] = norm
                return norm
    except Exception:
        return None
    return None


class MoleculeDrawer:
    """Handles molecule drawing using RDKit."""
    
    def __init__(self):
        """Initialize the molecule drawer."""
        # Set up RDKit for better 2D coordinate generation
        rdDepictor.SetPreferCoordGen(True)
    
    def validate_smiles(self, smiles: str) -> bool:
        """Validate if a SMILES string is valid."""
        try:
            mol = Chem.MolFromSmiles(smiles)
            return mol is not None
        except Exception:
            return False
    
    def draw_molecule_svg(self, smiles: str, name: str = "", width: int = 300, height: int = 300) -> Optional[str]:
        """
        Draw a molecule as SVG string.
        
        Args:
            smiles: SMILES string of the molecule
            name: Name of the molecule (for display)
            width: Width of the image
            height: Height of the image
            
        Returns:
            SVG string or None if failed
        """
        try:
            # Create molecule from SMILES
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                print(f"Failed to create molecule from SMILES: {smiles}")
                return None
            
            # Generate 2D coordinates
            rdDepictor.Compute2DCoords(mol)
            
            # Create SVG drawer
            drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
            drawer.SetFontSize(12)
            
            # Draw the molecule
            drawer.DrawMolecule(mol)
            drawer.FinishDrawing()
            
            # Get SVG string
            svg = drawer.GetDrawingText()
            
            # Add title if provided
            if name:
                # Insert title into SVG
                title_svg = f'<text x="{width//2}" y="20" text-anchor="middle" font-family="Arial" font-size="14" fill="#333">{name}</text>'
                svg = svg.replace('<svg', f'<svg><g>{title_svg}</g>', 1)
            
            return svg
            
        except Exception as e:
            print(f"Error drawing molecule {name} ({smiles}): {e}")
            return None
    
    def draw_molecule_png(self, smiles: str, name: str = "", width: int = 300, height: int = 300) -> Optional[bytes]:
        """
        Draw a molecule as PNG bytes.
        
        Args:
            smiles: SMILES string of the molecule
            name: Name of the molecule (for display)
            width: Width of the image
            height: Height of the image
            
        Returns:
            PNG bytes or None if failed
        """
        try:
            # Create molecule from SMILES
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                print(f"Failed to create molecule from SMILES: {smiles}")
                return None
            
            # Generate 2D coordinates
            rdDepictor.Compute2DCoords(mol)
            
            # Create PNG drawer
            drawer = rdMolDraw2D.MolDraw2DCairo(width, height)
            drawer.SetFontSize(12)
            
            # Draw the molecule
            drawer.DrawMolecule(mol)
            drawer.FinishDrawing()
            
            # Get PNG bytes
            png_bytes = drawer.GetDrawingText()
            
            return png_bytes
            
        except Exception as e:
            print(f"Error drawing molecule {name} ({smiles}): {e}")
            return None
    
    def draw_molecule_base64(self, smiles: str, name: str = "", width: int = 300, height: int = 300) -> Optional[str]:
        """
        Draw a molecule as base64-encoded PNG.
        
        Args:
            smiles: SMILES string of the molecule
            name: Name of the molecule (for display)
            width: Width of the image
            height: Height of the image
            
        Returns:
            Base64-encoded PNG string or None if failed
        """
        try:
            png_bytes = self.draw_molecule_png(smiles, name, width, height)
            if png_bytes is None:
                return None
            
            # Encode as base64
            base64_string = base64.b64encode(png_bytes).decode('utf-8')
            return f"data:image/png;base64,{base64_string}"
            
        except Exception as e:
            print(f"Error creating base64 image for {name} ({smiles}): {e}")
            return None
    
    def get_molecule_info(self, smiles: str) -> dict:
        """
        Get information about a molecule.
        
        Args:
            smiles: SMILES string of the molecule
            
        Returns:
            Dictionary with molecule information
        """
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return {"error": "Invalid SMILES string"}
            
            # Get molecular formula
            formula = Chem.rdMolDescriptors.CalcMolFormula(mol)
            
            # Get molecular weight
            mw = Chem.rdMolDescriptors.CalcExactMolWt(mol)
            
            # Get number of atoms
            num_atoms = mol.GetNumAtoms()
            
            # Get number of bonds
            num_bonds = mol.GetNumBonds()
            
            return {
                "formula": formula,
                "molecular_weight": round(mw, 2),
                "num_atoms": num_atoms,
                "num_bonds": num_bonds,
                "smiles": smiles,
                "valid": True
            }
            
        except Exception as e:
            return {"error": f"Error processing molecule: {e}"}


# Global instance
molecule_drawer = MoleculeDrawer()


def draw_molecule_svg(smiles: str, name: str = "", width: int = 300, height: int = 300) -> Optional[str]:
    """Convenience function to draw a molecule as SVG."""
    return molecule_drawer.draw_molecule_svg(smiles, name, width, height)


def draw_molecule_base64(smiles: str, name: str = "", width: int = 300, height: int = 300) -> Optional[str]:
    """Convenience function to draw a molecule as base64 PNG."""
    return molecule_drawer.draw_molecule_base64(smiles, name, width, height)


def get_molecule_info(smiles: str) -> dict:
    """Convenience function to get molecule information."""
    return molecule_drawer.get_molecule_info(smiles)
