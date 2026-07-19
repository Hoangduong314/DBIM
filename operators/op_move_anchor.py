import bpy
import gpu
from gpu_extras.batch import batch_for_shader
import math
import mathutils
from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d, location_3d_to_region_2d

LOCK_TOLERANCE = 0.01  # Distance threshold for perpendicular alignment (in Blender units)

def get_2d_shader():
    try:
        return gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    except:
        return gpu.shader.from_builtin('UNIFORM_COLOR')

def _clip_line_to_rect(x1, y1, x2, y2, xmin, ymin, xmax, ymax):
    """Cohen-Sutherland line clipping algorithm.
    Clips a line segment to a rectangle. Returns (x1,y1,x2,y2) or None.
    """
    INSIDE, LEFT, RIGHT, BOTTOM, TOP = 0, 1, 2, 4, 8
    def _code(x, y):
        c = INSIDE
        if x < xmin: c |= LEFT
        elif x > xmax: c |= RIGHT
        if y < ymin: c |= BOTTOM
        elif y > ymax: c |= TOP
        return c
    
    c1, c2 = _code(x1, y1), _code(x2, y2)
    while True:
        if not (c1 | c2):
            return (x1, y1, x2, y2)
        if c1 & c2:
            return None
        c = c1 or c2
        if c & TOP:
            x = x1 + (x2 - x1) * (ymax - y1) / (y2 - y1); y = ymax
        elif c & BOTTOM:
            x = x1 + (x2 - x1) * (ymin - y1) / (y2 - y1); y = ymin
        elif c & RIGHT:
            y = y1 + (y2 - y1) * (xmax - x1) / (x2 - x1); x = xmax
        elif c & LEFT:
            y = y1 + (y2 - y1) * (xmin - x1) / (x2 - x1); x = xmin
        if c == c1:
            x1, y1, c1 = x, y, _code(x, y)
        else:
            x2, y2, c2 = x, y, _code(x, y)

def find_locked_endpoints(target_obj, anchor_index):
    """Find all grid endpoints that lie on the perpendicular to the target grid
    passing through the moving anchor.
    
    The perpendicular check works as follows:
    - Target grid has direction D (from StartPoint to EndPoint).
    - The perpendicular line at anchor P_A goes in the direction N = perp(D).
    - For another endpoint P_B to be on this perpendicular:
      abs(dot(P_B - P_A, D)) < tolerance  (i.e. zero component along grid direction)
    
    Returns a list of tuples: (obj, endpoint_index) where endpoint_index is 0 (Start) or 1 (End).
    """
    if anchor_index == 0:
        anchor_pos = mathutils.Vector(target_obj.ifc_StartPoint)
    else:
        anchor_pos = mathutils.Vector(target_obj.ifc_EndPoint)
    
    # Grid direction (2D, XY plane)
    sp = mathutils.Vector(target_obj.ifc_StartPoint)
    ep = mathutils.Vector(target_obj.ifc_EndPoint)
    grid_dir_2d = (ep.xy - sp.xy)
    if grid_dir_2d.length < 1e-6:
        return []
    grid_dir_2d = grid_dir_2d.normalized()
    
    locked = []
    for obj in bpy.context.scene.objects:
        if obj == target_obj:
            continue
        if not (getattr(obj, "is_IfcGridAxis", False) or getattr(obj, "is_IfcWall", False)):
            continue
        if not hasattr(obj, "ifc_StartPoint") or not hasattr(obj, "ifc_EndPoint"):
            continue
            
        obj_sp = mathutils.Vector(obj.ifc_StartPoint)
        obj_ep = mathutils.Vector(obj.ifc_EndPoint)
        
        # Check StartPoint: is it on the perpendicular to our grid at anchor_pos?
        delta_sp = obj_sp.xy - anchor_pos.xy
        if abs(delta_sp.dot(grid_dir_2d)) < LOCK_TOLERANCE:
            locked.append((obj, 0))
        
        # Check EndPoint
        delta_ep = obj_ep.xy - anchor_pos.xy
        if abs(delta_ep.dot(grid_dir_2d)) < LOCK_TOLERANCE:
            locked.append((obj, 1))
    
    return locked

class DBIM_OT_move_anchor(bpy.types.Operator):
    """Move Anchor (Custom Snap Engine) with Auto-Lock"""
    bl_idname = "dbim.move_anchor"
    bl_label = "Move Anchor"
    bl_options = {'REGISTER', 'UNDO'}

    anchor_index: bpy.props.IntProperty(name="Anchor Index", default=0)
    
    _handle = None
    snap_point_3d = None
    extend_mode = False
    lock_enabled = True

    def invoke(self, context, event):
        self.target_obj = context.active_object
        if not self.target_obj: return {'CANCELLED'}
        if self.target_obj.get("dbim_is_moving_anchor", False): return {'CANCELLED'}
        self.target_obj["dbim_is_moving_anchor"] = True

        self.initial_loc = tuple(self.target_obj.ifc_StartPoint) if self.anchor_index == 0 else tuple(self.target_obj.ifc_EndPoint)
        self.initial_z = self.initial_loc[2]
        
        # Grid line definition for extension
        sp = mathutils.Vector(self.target_obj.ifc_StartPoint)
        ep = mathutils.Vector(self.target_obj.ifc_EndPoint)
        self.grid_dir = (ep - sp).normalized()
        self.grid_origin = sp
        
        self.extend_mode = True
        self.lock_enabled = True
        self.snap_point_3d = None
        self._state = 0

        # Find locked endpoints BEFORE moving
        self.locked_endpoints = find_locked_endpoints(self.target_obj, self.anchor_index)
        # Store initial positions for undo
        self.locked_initial = []
        for obj, idx in self.locked_endpoints:
            if idx == 0:
                self.locked_initial.append(tuple(obj.ifc_StartPoint))
            else:
                self.locked_initial.append(tuple(obj.ifc_EndPoint))

        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if not getattr(self, 'target_obj', None) or self.target_obj.name not in bpy.data.objects:
            self.cleanup(context)
            return {'FINISHED'}

        # PASS THROUGH NAVIGATION EVENTS
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'TRACKPADPAN', 'TRACKPADZOOM', 'NUMPAD_1', 'NUMPAD_3', 'NUMPAD_7', 'NUMPAD_5'}:
            return {'PASS_THROUGH'}

        if self._state == 0:
            if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
                self._state = 1
            return {'PASS_THROUGH'}

        # TAB: Toggle extend mode (free vs along-grid)
        if event.type == 'TAB' and event.value == 'PRESS':
            self.extend_mode = not self.extend_mode
            # Re-enable lock when switching back to extend mode
            if self.extend_mode and not self.lock_enabled and self.locked_endpoints:
                self.lock_enabled = True
                self.report({'INFO'}, "Grid Lock: ON")
            context.area.tag_redraw()
            return {'RUNNING_MODAL'}
        
        # L key: Toggle lock on/off
        if event.type == 'L' and event.value == 'PRESS':
            self.lock_enabled = not self.lock_enabled
            context.area.tag_redraw()
            self.report({'INFO'}, f"Grid Lock: {'ON' if self.lock_enabled else 'OFF'}")
            return {'RUNNING_MODAL'}

        if event.type == 'MOUSEMOVE':
            region = context.region
            rv3d = context.region_data
            coord = (event.mouse_region_x, event.mouse_region_y)
            view_vector = region_2d_to_vector_3d(region, rv3d, coord)
            ray_origin = region_2d_to_origin_3d(region, rv3d, coord)
            
            # Base intersection on Z = initial_z
            if abs(view_vector.z) > 1e-6:
                t = (self.initial_z - ray_origin.z) / view_vector.z
                loc = ray_origin + view_vector * t
            else:
                loc = mathutils.Vector(self.initial_loc)

            # Snap logic
            self.snap_point_3d = None
            if context.scene.tool_settings.use_snap:
                closest_dist = 20.0
                closest_point = None
                
                # Check DBIM objects
                for obj in context.scene.objects:
                    if getattr(obj, "is_IfcWall", False) or getattr(obj, "is_IfcGridAxis", False):
                        if hasattr(obj, "ifc_StartPoint"):
                            sp_v = mathutils.Vector(obj.ifc_StartPoint)
                            sp_2d = location_3d_to_region_2d(region, rv3d, sp_v)
                            if sp_2d and (sp_2d - mathutils.Vector(coord)).length < closest_dist:
                                if obj != self.target_obj or self.anchor_index != 0:
                                    closest_dist = (sp_2d - mathutils.Vector(coord)).length
                                    closest_point = sp_v
                        if hasattr(obj, "ifc_EndPoint"):
                            ep_v = mathutils.Vector(obj.ifc_EndPoint)
                            ep_2d = location_3d_to_region_2d(region, rv3d, ep_v)
                            if ep_2d and (ep_2d - mathutils.Vector(coord)).length < closest_dist:
                                if obj != self.target_obj or self.anchor_index != 1:
                                    closest_dist = (ep_2d - mathutils.Vector(coord)).length
                                    closest_point = ep_v
                                    
                # Check scene geometry
                if not closest_point:
                    hit, hit_loc, normal, index, hit_obj, matrix = context.scene.ray_cast(context.view_layer.depsgraph, ray_origin, view_vector)
                    if hit:
                        mesh = hit_obj.data
                        if isinstance(mesh, bpy.types.Mesh):
                            poly = mesh.polygons[index]
                            min_d = 9999
                            for loop_idx in poly.loop_indices:
                                v_idx = mesh.loops[loop_idx].vertex_index
                                v_loc = hit_obj.matrix_world @ mesh.vertices[v_idx].co
                                v_2d = location_3d_to_region_2d(region, rv3d, v_loc)
                                if v_2d:
                                    dist = (v_2d - mathutils.Vector(coord)).length
                                    if dist < closest_dist and dist < min_d:
                                        min_d = dist
                                        closest_dist = dist
                                        closest_point = v_loc
                        if not closest_point:
                            closest_point = hit_loc

                if closest_point:
                    loc = closest_point
                    self.snap_point_3d = closest_point

            # Apply constraints
            if self.extend_mode:
                v = loc - self.grid_origin
                proj_len = v.dot(self.grid_dir)
                loc = self.grid_origin + self.grid_dir * proj_len

            # AUTO-LOCK CHECK: disengage lock when dragging off-axis
            if self.lock_enabled and self.locked_endpoints:
                delta = mathutils.Vector((loc.x - self.initial_loc[0], loc.y - self.initial_loc[1]))
                if delta.length > 0.01:
                    # Perpendicular distance from grid line
                    perp_dist = abs(delta.x * (-self.grid_dir.y) + delta.y * self.grid_dir.x)
                    if perp_dist > 0.05:
                        # Dragged off-axis: auto-unlock and restore locked endpoints
                        self.lock_enabled = False
                        for i, (obj, idx) in enumerate(self.locked_endpoints):
                            if obj.name not in bpy.data.objects:
                                continue
                            orig = self.locked_initial[i]
                            if idx == 0:
                                obj.ifc_StartPoint = orig
                            else:
                                obj.ifc_EndPoint = orig
                            obj.update_tag()
                        self.report({'INFO'}, "Grid Lock: AUTO OFF (dragged off-axis)")

            # APPLY RESULT to target
            if self.anchor_index == 0:
                self.target_obj.ifc_StartPoint = (loc.x, loc.y, self.initial_z)
            else:
                self.target_obj.ifc_EndPoint = (loc.x, loc.y, self.initial_z)
            self.target_obj.update_tag()
            
            # APPLY RESULT to locked endpoints using DELTA displacement
            if self.lock_enabled and self.locked_endpoints:
                delta_x = loc.x - self.initial_loc[0]
                delta_y = loc.y - self.initial_loc[1]
                for i, (obj, idx) in enumerate(self.locked_endpoints):
                    if obj.name not in bpy.data.objects:
                        continue
                    orig = self.locked_initial[i]
                    if idx == 0:
                        obj.ifc_StartPoint = (orig[0] + delta_x, orig[1] + delta_y, orig[2])
                    else:
                        obj.ifc_EndPoint = (orig[0] + delta_x, orig[1] + delta_y, orig[2])
                    obj.update_tag()
            
            context.area.tag_redraw()

        elif event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'ESC', 'RET'} and event.value == 'PRESS':
            if event.type in {'RIGHTMOUSE', 'ESC'}:
                # Undo: restore target
                if self.anchor_index == 0: self.target_obj.ifc_StartPoint = self.initial_loc
                else: self.target_obj.ifc_EndPoint = self.initial_loc
                self.target_obj.update_tag()
                # Undo: restore locked
                for i, (obj, idx) in enumerate(self.locked_endpoints):
                    if obj.name not in bpy.data.objects:
                        continue
                    if idx == 0:
                        obj.ifc_StartPoint = self.locked_initial[i]
                    else:
                        obj.ifc_EndPoint = self.locked_initial[i]
                    obj.update_tag()
                    
            self.cleanup(context)
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def cleanup(self, context):
        if getattr(self, 'target_obj', None):
            self.target_obj["dbim_is_moving_anchor"] = False
            self.target_obj.select_set(True)
            context.view_layer.objects.active = self.target_obj
            
        if getattr(self, '_handle', None):
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self._handle = None
            
        context.area.tag_redraw()

    def draw_callback_px(self, self_ref, context):
        shader = get_2d_shader()
        shader.bind()
        
        # 1. Draw Orange Circle if snapped
        if getattr(self_ref, 'snap_point_3d', None):
            pos_2d = location_3d_to_region_2d(context.region, context.region_data, self_ref.snap_point_3d)
            if pos_2d:
                segments = 16
                radius = 7.0
                coords = []
                for i in range(segments):
                    angle = (i * 2 * math.pi) / segments
                    coords.append((pos_2d.x + math.cos(angle) * radius, pos_2d.y + math.sin(angle) * radius))
                    angle_next = ((i + 1) * 2 * math.pi) / segments
                    coords.append((pos_2d.x + math.cos(angle_next) * radius, pos_2d.y + math.sin(angle_next) * radius))
                coords.extend([
                    (pos_2d.x - radius, pos_2d.y), (pos_2d.x + radius, pos_2d.y),
                    (pos_2d.x, pos_2d.y - radius), (pos_2d.x, pos_2d.y + radius)
                ])
                batch = batch_for_shader(shader, 'LINES', {"pos": coords})
                shader.uniform_float("color", (1.0, 0.5, 0.0, 1.0))
                gpu.state.line_width_set(2.0)
                batch.draw(shader)
                gpu.state.line_width_set(1.0)
                
        # 2. Draw Extension Tracking Line as CENTER LINE (long-short-long dashed)
        if getattr(self_ref, 'extend_mode', False):
            region = context.region
            rv3d = context.region_data
            
            p1 = self_ref.grid_origin - self_ref.grid_dir * 1000
            p2 = self_ref.grid_origin + self_ref.grid_dir * 1000
            p1_2d = location_3d_to_region_2d(region, rv3d, p1)
            p2_2d = location_3d_to_region_2d(region, rv3d, p2)
            if p1_2d and p2_2d:
                # Calculate VIEW SCALE (pixels per meter) at grid origin
                origin = self_ref.grid_origin
                offset = origin + mathutils.Vector((1, 0, 0))
                o_2d = location_3d_to_region_2d(region, rv3d, origin)
                off_2d = location_3d_to_region_2d(region, rv3d, offset)
                if o_2d and off_2d:
                    px_per_meter = (off_2d - o_2d).length
                else:
                    px_per_meter = 100.0  # fallback
                
                # Dash sizes in METERS (consistent regardless of zoom)
                long_dash_m = 0.2
                short_dash_m = 0.04
                gap_m = 0.06
                
                # Convert to pixels using view scale
                long_dash = long_dash_m * px_per_meter
                short_dash = short_dash_m * px_per_meter
                gap = gap_m * px_per_meter
                
                # Clamp dash sizes to reasonable pixel range
                long_dash = max(8.0, min(long_dash, 60.0))
                short_dash = max(2.0, min(short_dash, 12.0))
                gap = max(3.0, min(gap, 20.0))
                
                # Clip line to viewport bounds
                w = region.width
                h = region.height
                clipped = _clip_line_to_rect(p1_2d.x, p1_2d.y, p2_2d.x, p2_2d.y, 0, 0, w, h)
                if clipped:
                    cx1, cy1, cx2, cy2 = clipped
                    dx = cx2 - cx1
                    dy = cy2 - cy1
                    line_len = math.sqrt(dx * dx + dy * dy)
                    if line_len > 1:
                        nx = dx / line_len
                        ny = dy / line_len
                        
                        dashes = []
                        t = 0.0
                        while t < line_len:
                            # Long dash
                            t_end = min(t + long_dash, line_len)
                            dashes.append((cx1 + nx * t, cy1 + ny * t))
                            dashes.append((cx1 + nx * t_end, cy1 + ny * t_end))
                            t = t_end + gap
                            if t >= line_len:
                                break
                            # Short dash (dot)
                            t_end = min(t + short_dash, line_len)
                            dashes.append((cx1 + nx * t, cy1 + ny * t))
                            dashes.append((cx1 + nx * t_end, cy1 + ny * t_end))
                            t = t_end + gap
                        
                        if dashes:
                            batch = batch_for_shader(shader, 'LINES', {"pos": dashes})
                            shader.uniform_float("color", (1.0, 0.2, 0.2, 0.7))
                            gpu.state.line_width_set(1.5)
                            batch.draw(shader)
                            gpu.state.line_width_set(1.0)

        # 3. Draw Lock indicators on locked endpoints
        if getattr(self_ref, 'locked_endpoints', None) and getattr(self_ref, 'lock_enabled', True):
            for (obj, idx) in self_ref.locked_endpoints:
                if obj.name not in bpy.data.objects:
                    continue
                pt = mathutils.Vector(obj.ifc_StartPoint) if idx == 0 else mathutils.Vector(obj.ifc_EndPoint)
                pt_2d = location_3d_to_region_2d(context.region, context.region_data, pt)
                if pt_2d:
                    # Draw a small cyan diamond
                    s = 5.0
                    diamond = [
                        (pt_2d.x, pt_2d.y + s), (pt_2d.x + s, pt_2d.y),
                        (pt_2d.x + s, pt_2d.y), (pt_2d.x, pt_2d.y - s),
                        (pt_2d.x, pt_2d.y - s), (pt_2d.x - s, pt_2d.y),
                        (pt_2d.x - s, pt_2d.y), (pt_2d.x, pt_2d.y + s),
                    ]
                    batch = batch_for_shader(shader, 'LINES', {"pos": diamond})
                    shader.uniform_float("color", (0.0, 1.0, 1.0, 0.8))
                    gpu.state.line_width_set(2.0)
                    batch.draw(shader)
                    gpu.state.line_width_set(1.0)
