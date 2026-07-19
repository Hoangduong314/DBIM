import bpy

def create_grid_mesh(p1, p2, name):
    """
    Generate a Grease Pencil object for a grid line.
    This creates a pickable line (via the base stroke) that is drawn dashed
    using the Dash modifier, solving both picking and visibility issues.
    """
    gp_name = f"IfcGridAxis_{name}"
    
    try:
        gp_data = bpy.data.grease_pencils.new(gp_name)
    except Exception:
        # Fallback if Grease Pencil creation fails for some reason
        return None
        
    obj = bpy.data.objects.new(gp_name, gp_data)
    
    # Setup material (red center line color)
    mat = bpy.data.materials.new(name=f"CenterLine_{name}")
    bpy.data.materials.create_gpencil_data(mat)
    mat.grease_pencil.color = (0.8, 0.2, 0.2, 1.0)
    mat.grease_pencil.show_fill = False
    gp_data.materials.append(mat)
    
    # Create layer
    layer = gp_data.layers.new("CenterLine")
    
    try:
        scale_val = int(bpy.context.scene.dbim_view_scale)
    except:
        scale_val = 100
    scale_factor = scale_val / 100.0
    
    # Add Dash modifier
    mod = obj.grease_pencil_modifiers.new("Dash", 'GP_DASH')
    if hasattr(mod, 'segments') and len(mod.segments) > 0:
        seg = mod.segments[0]
        seg.dash = max(2, int(15 / scale_factor))
        seg.gap = max(1, int(4 / scale_factor))
        mod.segment_add()
        if len(mod.segments) > 1:
            seg2 = mod.segments[1]
            seg2.dash = max(1, int(3 / scale_factor))
            seg2.gap = max(1, int(4 / scale_factor))
            
    # Add Thickness modifier
    thick_mod = obj.grease_pencil_modifiers.new("Thickness", 'GP_THICK')
    thick_mod.thickness_factor = 1.5
    
    # Create frame and stroke
    frame = layer.frames.new(0)
    stroke = frame.strokes.new()
    stroke.line_width = 30
    stroke.material_index = 0
    
    stroke.points.add(2)
    stroke.points[0].co = p1
    stroke.points[0].pressure = 1.0
    stroke.points[0].strength = 1.0
    stroke.points[1].co = p2
    stroke.points[1].pressure = 1.0
    stroke.points[1].strength = 1.0
    
    return obj
