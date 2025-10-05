"""
Molecule drawing module using RDKit for server-side molecule rendering.
This provides reliable molecule diagram generation without browser dependencies.
"""

import base64
import io
from typing import Optional, Tuple
from rdkit import Chem
from rdkit.Chem import Draw, rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D
from PIL import Image


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
