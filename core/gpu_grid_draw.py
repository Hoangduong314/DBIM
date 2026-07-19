import bpy
import gpu
from gpu_extras.batch import batch_for_shader

_handle = None

def draw_grids_3d():
    # Only draw if overlays are enabled
    if not bpy.context.space_data.overlay.show_overlays:
        return
        
    try:
        scale_val = int(bpy.context.scene.dbim_view_scale)
    except:
        scale_val = 100
        
    scale_factor = scale_val / 100.0

    lines = []
    
    # Collect all grid segments
    for obj in bpy.context.scene.objects:
        if getattr(obj, "is_IfcGridAxis", False) and obj.type == 'MESH':
            # Use the properties instead of geometry to guarantee accurate endpoints
            try:
                p1 = obj.matrix_world @ bpy.mathutils.Vector(obj.ifc_StartPoint)
                p2 = obj.matrix_world @ bpy.mathutils.Vector(obj.ifc_EndPoint)
                lines.append((p1, p2))
            except:
                pass

    if not lines:
        return

    # Generate Dash points (Dot Dash pattern: Long Dash - short gap - short dash - short gap)
    dash_long = 15.0 / scale_factor
    gap_short = 4.0 / scale_factor
    dash_short = 3.0 / scale_factor
    
    # We will compute the segments in 3D space.
    # Note: A true screen-space dashed line requires a custom shader, 
    # but calculating world-space dashes based on a fixed scale is often good enough for CAD.
    
    dash_verts = []
    
    for p1, p2 in lines:
        direction = p2 - p1
        total_length = direction.length
        if total_length == 0:
            continue
            
        dir_norm = direction / total_length
        current_pos = 0.0
        
        # Pattern sequence: long dash, gap, short dash, gap
        pattern = [(dash_long, True), (gap_short, False), (dash_short, True), (gap_short, False)]
        pattern_len = len(pattern)
        pi = 0
        
        while current_pos < total_length:
            seg_len, is_solid = pattern[pi % pattern_len]
            
            end_pos = min(current_pos + seg_len, total_length)
            
            if is_solid:
                dash_verts.append(p1 + dir_norm * current_pos)
                dash_verts.append(p1 + dir_norm * end_pos)
                
            current_pos = end_pos
            pi += 1

    if not dash_verts:
        return

    try:
        if bpy.app.version >= (4, 0, 0):
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    except:
        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')

    batch = batch_for_shader(shader, 'LINES', {"pos": dash_verts})

    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(1.5)
    
    # Optional: depth_test_set('NONE') if you want grids to show through objects
    # gpu.state.depth_test_set('NONE')

    shader.bind()
    shader.uniform_float("color", (0.8, 0.2, 0.2, 1.0)) # Red dashed line
    batch.draw(shader)
    
    gpu.state.blend_set('NONE')
    gpu.state.line_width_set(1.0)
    # gpu.state.depth_test_set('LESS_EQUAL')


def register():
    global _handle
    if _handle is None:
        _handle = bpy.types.SpaceView3D.draw_handler_add(draw_grids_3d, (), 'WINDOW', 'POST_VIEW')

def unregister():
    global _handle
    if _handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')
        _handle = None
