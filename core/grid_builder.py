import bpy
import bmesh

def create_grid_mesh(p1, p2, name):
    """
    Generate a mesh object for a grid line (single edge)
    with a Grease Pencil child for center line visual (dashed).
    """
    bm = bmesh.new()
    
    # Create two vertices and an edge
    v1 = bm.verts.new(p1)
    v2 = bm.verts.new(p2)
    bm.edges.new((v1, v2))
    
    mesh = bpy.data.meshes.new(name=f"IfcGridAxis_{name}")
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new(f"IfcGridAxis_{name}", mesh)
    
    # Hide the mesh wireframe, display via GP instead
    obj.display_type = 'WIRE'
    
    return obj

def create_grid_gp(grid_obj, p1, p2):
    """Create or update a Grease Pencil child for dashed center line display."""
    gp_name = f"GP_{grid_obj.name}"
    
    # Check if GP child already exists
    gp_obj = None
    for child in grid_obj.children:
        if child.type == 'GREASEPENCIL' and child.name.startswith("GP_"):
            gp_obj = child
            break
    
    if gp_obj is None:
        # Create new GP object
        try:
            gp_data = bpy.data.grease_pencils.new(gp_name)
        except Exception:
            # Blender 5.x may use different API
            return None
        
        gp_obj = bpy.data.objects.new(gp_name, gp_data)
        
        # Link to same collection as grid
        for col in grid_obj.users_collection:
            col.objects.link(gp_obj)
            break
        
        # Parent to grid (no transform inheritance so GP stays at world origin)
        gp_obj.parent = grid_obj
        gp_obj.matrix_parent_inverse = grid_obj.matrix_world.inverted()
        
        # Make GP non-selectable so it doesn't interfere
        gp_obj.hide_select = True
        
        # Setup material (red center line color)
        mat = bpy.data.materials.new(name=f"CenterLine_{grid_obj.name}")
        bpy.data.materials.create_gpencil_data(mat)
        mat.grease_pencil.color = (0.8, 0.2, 0.2, 1.0)
        mat.grease_pencil.show_fill = False
        gp_data.materials.append(mat)
        
        # Create layer
        layer = gp_data.layers.new("CenterLine")
        layer.line_change = 0
        
        # Add Dash modifier for center line pattern
        mod = gp_obj.grease_pencil_modifiers.new("Dash", 'GP_DASH')
        # Configure dash segments: long dash - gap - short dash - gap
        # Default segment exists, modify it
        if hasattr(mod, 'segments') and len(mod.segments) > 0:
            seg = mod.segments[0]
            seg.dash = 15     # long dash length
            seg.gap = 4       # gap after long dash
            # Add second segment for short dash
            mod.segment_add()
            if len(mod.segments) > 1:
                seg2 = mod.segments[1]
                seg2.dash = 3   # short dash (dot)
                seg2.gap = 4    # gap after dot
        
        # Add Thickness modifier for line width
        thick_mod = gp_obj.grease_pencil_modifiers.new("Thickness", 'GP_THICK')
        thick_mod.thickness_factor = 1.5
    
    # Update stroke points
    gp_data = gp_obj.data
    if len(gp_data.layers) > 0:
        layer = gp_data.layers[0]
        
        # Clear existing frames
        for frame in list(layer.frames):
            layer.frames.remove(frame)
        
        # Create new frame with stroke
        frame = layer.frames.new(0)
        stroke = frame.strokes.new()
        stroke.line_width = 30  # base line width in pixels
        stroke.material_index = 0
        
        stroke.points.add(2)
        stroke.points[0].co = p1
        stroke.points[0].pressure = 1.0
        stroke.points[0].strength = 1.0
        stroke.points[1].co = p2
        stroke.points[1].pressure = 1.0
        stroke.points[1].strength = 1.0
    
    return gp_obj

def update_grid_gp(grid_obj):
    """Update the GP child to match current grid endpoints."""
    import mathutils
    p1 = mathutils.Vector(grid_obj.ifc_StartPoint)
    p2 = mathutils.Vector(grid_obj.ifc_EndPoint)
    create_grid_gp(grid_obj, p1, p2)

def set_grid_gp_visibility(grid_obj, visible):
    """Hide or show the GP child of a grid object."""
    for child in grid_obj.children:
        if child.type == 'GREASEPENCIL' and child.name.startswith("GP_"):
            child.hide_viewport = not visible
            break

def remove_grid_gp(grid_obj):
    """Remove the GP child from a grid object."""
    for child in list(grid_obj.children):
        if child.type == 'GREASEPENCIL' and child.name.startswith("GP_"):
            bpy.data.objects.remove(child, do_unlink=True)
