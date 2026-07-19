import bpy
import bmesh

def create_grid_mesh(p1, p2, name):
    """
    Generate a mesh object for a grid line.
    The edge is hidden so it doesn't draw, but exists for snapping.
    A Grease Pencil child is created for visual and selection.
    """
    bm = bmesh.new()
    v1 = bm.verts.new(p1)
    v2 = bm.verts.new(p2)
    e = bm.edges.new((v1, v2))
    e.hide = True # Hide in viewport!
    
    mesh = bpy.data.meshes.new(name=f"IfcGridAxis_{name}")
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new(f"IfcGridAxis_{name}", mesh)
    obj.display_type = 'WIRE'
    
    create_grid_gp(obj, p1, p2)
    return obj

def create_grid_gp(grid_obj, p1, p2):
    """Create a Grease Pencil child for dashed center line display."""
    gp_name = f"GP_{grid_obj.name}"
    
    gp_obj = None
    for child in grid_obj.children:
        if child.type == 'GREASEPENCIL' and child.name.startswith("GP_"):
            gp_obj = child
            break
            
    if gp_obj is None:
        try:
            gp_data = bpy.data.grease_pencils.new(gp_name)
        except Exception:
            return None
        
        gp_obj = bpy.data.objects.new(gp_name, gp_data)
        
        for col in grid_obj.users_collection:
            col.objects.link(gp_obj)
            break
            
        gp_obj.parent = grid_obj
        gp_obj.matrix_parent_inverse = grid_obj.matrix_world.inverted()
        gp_obj.hide_select = False # Allow selection to trigger our handler!
        
        mat = bpy.data.materials.new(name=f"CenterLine_{grid_obj.name}")
        bpy.data.materials.create_gpencil_data(mat)
        mat.grease_pencil.color = (0.8, 0.2, 0.2, 1.0)
        mat.grease_pencil.show_fill = False
        gp_data.materials.append(mat)
        
        layer = gp_data.layers.new("CenterLine")
        layer.line_change = 0
        
        mod = gp_obj.grease_pencil_modifiers.new("Dash", 'GP_DASH')
        if hasattr(mod, 'segments') and len(mod.segments) > 0:
            seg = mod.segments[0]
            seg.dash = 15
            seg.gap = 4
            mod.segment_add()
            if len(mod.segments) > 1:
                seg2 = mod.segments[1]
                seg2.dash = 3
                seg2.gap = 4
                
        thick_mod = gp_obj.grease_pencil_modifiers.new("Thickness", 'GP_THICK')
        thick_mod.thickness_factor = 1.5

    try:
        scale_val = int(bpy.context.scene.dbim_view_scale)
    except:
        scale_val = 100
    
    scale_factor = scale_val / 100.0
    
    mod = gp_obj.grease_pencil_modifiers.get("Dash")
    if mod and hasattr(mod, 'segments') and len(mod.segments) > 1:
        mod.segments[0].dash = max(2, int(15 / scale_factor))
        mod.segments[0].gap = max(1, int(4 / scale_factor))
        mod.segments[1].dash = max(1, int(3 / scale_factor))
        mod.segments[1].gap = max(1, int(4 / scale_factor))
        
    gp_data = gp_obj.data
    if len(gp_data.layers) > 0:
        layer = gp_data.layers[0]
        if len(layer.frames) > 0:
            frame = layer.frames[0]
            frame.clear()
        else:
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
    
    return gp_obj

def update_grid_gp(grid_obj):
    import mathutils
    p1 = mathutils.Vector(grid_obj.ifc_StartPoint)
    p2 = mathutils.Vector(grid_obj.ifc_EndPoint)
    create_grid_gp(grid_obj, p1, p2)

def set_grid_gp_visibility(grid_obj, visible):
    for child in grid_obj.children:
        if child.type == 'GREASEPENCIL' and child.name.startswith("GP_"):
            child.hide_viewport = not visible
            break

from bpy.app.handlers import persistent

@persistent
def enforce_grid_selection(scene):
    """
    If the user clicks the Grease Pencil dashed line, 
    automatically switch the selection to the parent Grid mesh.
    """
    obj = bpy.context.active_object
    if obj and obj.type == 'GREASEPENCIL' and obj.name.startswith("GP_IfcGridAxis_"):
        if obj.parent and obj.parent.name in bpy.data.objects:
            try:
                obj.select_set(False)
                obj.parent.select_set(True)
                bpy.context.view_layer.objects.active = obj.parent
            except Exception:
                pass

def register():
    if enforce_grid_selection not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(enforce_grid_selection)

def unregister():
    if enforce_grid_selection in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(enforce_grid_selection)
