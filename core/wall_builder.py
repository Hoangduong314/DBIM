import bpy
import bmesh
import mathutils
from . import math_utils

def create_wall_mesh(points, height, layers):
    """
    Generate a mesh object for a wall based on a list of points (mathutils.Vector)
    and a list of IfcWallLayerItem.
    """
    if len(points) < 2:
        return None
        
    bm = bmesh.new()
    
    # Calculate total thickness
    total_thickness = sum(layer.thickness for layer in layers)
    if total_thickness == 0:
        total_thickness = 0.1 # Fallback
        
    # We will offset layers from the center line
    # Alternatively, offset from one side. Let's do center line for now.
    current_offset = -total_thickness / 2.0
    
    material_indices = []
    
    for layer_idx, layer in enumerate(layers):
        thickness = layer.thickness
        # Calculate offset for this specific layer
        layer_start_offset = current_offset
        layer_end_offset = current_offset + thickness
        
        # Build vertices for this layer
        bottom_verts = []
        top_verts = []
        
        for i in range(len(points)):
            p = points[i]
            
            # Find the perpendicular direction at this point
            if i == 0:
                perp = math_utils.get_perpendicular_2d(points[0], points[1])
            elif i == len(points) - 1:
                perp = math_utils.get_perpendicular_2d(points[i-1], points[i])
            else:
                # Average of perpendiculars
                perp1 = math_utils.get_perpendicular_2d(points[i-1], points[i])
                perp2 = math_utils.get_perpendicular_2d(points[i], points[i+1])
                perp = (perp1 + perp2).normalized()
                
                # We should actually calculate line intersection for perfect corners
                # For simplicity in this first version, we use average normal
            
            # Offset vertices
            v1_pos = p + perp * layer_start_offset
            v2_pos = p + perp * layer_end_offset
            
            bv1 = bm.verts.new(v1_pos)
            bv2 = bm.verts.new(v2_pos)
            tv1 = bm.verts.new(v1_pos + mathutils.Vector((0, 0, height)))
            tv2 = bm.verts.new(v2_pos + mathutils.Vector((0, 0, height)))
            
            bottom_verts.append((bv1, bv2))
            top_verts.append((tv1, tv2))
            
        # Create faces for this layer
        for i in range(len(points) - 1):
            bv1_a, bv2_a = bottom_verts[i]
            bv1_b, bv2_b = bottom_verts[i+1]
            tv1_a, tv2_a = top_verts[i]
            tv1_b, tv2_b = top_verts[i+1]
            
            # Bottom face
            f_bottom = bm.faces.new((bv1_a, bv2_a, bv2_b, bv1_b))
            # Top face
            f_top = bm.faces.new((tv1_b, tv2_b, tv2_a, tv1_a))
            # Side 1
            f_side1 = bm.faces.new((bv1_a, bv1_b, tv1_b, tv1_a))
            # Side 2
            f_side2 = bm.faces.new((bv2_b, bv2_a, tv2_a, tv2_b))
            
            f_bottom.material_index = layer_idx
            f_top.material_index = layer_idx
            f_side1.material_index = layer_idx
            f_side2.material_index = layer_idx
            
            # End caps
            if i == 0:
                f_cap1 = bm.faces.new((bv2_a, bv1_a, tv1_a, tv2_a))
                f_cap1.material_index = layer_idx
            if i == len(points) - 2:
                f_cap2 = bm.faces.new((bv1_b, bv2_b, tv2_b, tv1_b))
                f_cap2.material_index = layer_idx

        current_offset += thickness

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    
    mesh = bpy.data.meshes.new(name="IfcWall")
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new("IfcWall", mesh)
    
    # Assign materials
    for layer in layers:
        if layer.material:
            obj.data.materials.append(layer.material)
        else:
            # Create a dummy material or leave empty slot
            mat = bpy.data.materials.new(name=layer.name)
            obj.data.materials.append(mat)
            
    return obj
