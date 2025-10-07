"""
Molecule API Routes
Handles molecule drawing and information endpoints
"""
import json
from flask import Blueprint, request, Response

from backend.services.molecule_drawer import (
    draw_molecule_svg,
    draw_molecule_base64,
    get_molecule_info,
    resolve_curated_or_candidate,
)

molecule_bp = Blueprint('molecule', __name__)


@molecule_bp.route('/draw-molecule', methods=['POST', 'OPTIONS'])
def api_draw_molecule():
    """Draw molecules using server-side RDKit"""
    if request.method == 'OPTIONS':
        return Response(status=200)
    
    try:
        data = request.get_json(silent=True) or {}
        raw_smiles = data.get('smiles', '').strip()
        name = data.get('name', '').strip()
        format_type = data.get('format', 'svg')  # 'svg' or 'base64'
        width = int(data.get('width', 300))
        height = int(data.get('height', 300))
        
        # Resolve best SMILES from curated map or candidate
        smiles, source = resolve_curated_or_candidate(name, raw_smiles)
        if not smiles:
            return Response("Missing or invalid SMILES", status=400)
        
        if format_type == 'svg':
            # Return SVG
            svg_content = draw_molecule_svg(smiles, name, width, height)
            if svg_content:
                # Attach source as comment for debugging
                svg_with_meta = f"<!-- source:{source} name:{name} -->\n" + svg_content
                return Response(svg_with_meta, mimetype="image/svg+xml")
            else:
                return Response("Failed to generate molecule diagram", status=500)
        
        elif format_type == 'base64':
            # Return base64 PNG
            base64_content = draw_molecule_base64(smiles, name, width, height)
            if base64_content:
                return Response(base64_content, mimetype="text/plain")
            else:
                return Response("Failed to generate molecule diagram", status=500)
        
        else:
            return Response("Invalid format. Use 'svg' or 'base64'", status=400)
            
    except Exception as e:
        print(f"Error in draw-molecule API: {e}")
        return Response(f"Error: {str(e)}", status=500)


@molecule_bp.route('/molecule-info', methods=['POST', 'OPTIONS'])
def api_molecule_info():
    """Get molecule information"""
    if request.method == 'OPTIONS':
        return Response(status=200)
    
    try:
        data = request.get_json(silent=True) or {}
        smiles = data.get('smiles', '').strip()
        
        if not smiles:
            return Response("Missing SMILES string", status=400)
        
        info = get_molecule_info(smiles)
        return Response(json.dumps(info), mimetype="application/json")
        
    except Exception as e:
        print(f"Error in molecule-info API: {e}")
        return Response(f"Error: {str(e)}", status=500)

