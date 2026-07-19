import bpy
import gpu
from gpu_extras.batch import batch_for_shader
import math
import mathutils
from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d, location_3d_to_region_2d

def get_2d_shader():
    try:
        return gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    except:
        return gpu.shader.from_builtin('UNIFORM_COLOR')

class DBIM_OT_move_anchor(bpy.types.Operator):
    """Move Anchor (Click-Move-Click) with Custom DBIM Snap Engine"""
    bl_idname = "dbim.move_anchor"
    bl_label = "Move Anchor"
    bl_options = {'REGISTER', 'UNDO'}

    anchor_index: bpy.props.IntProperty(name="Anchor Index", default=0) # 0 for start, 1 for end
    
    _timer = None
    _state = 0 # 0: wait initial release, 1: transforming
    
    # Visual feedback
    _handle = None
    snap_point_3d = None

    def invoke(self, context, event):
        self.target_obj = context.active_object
        if not self.target_obj:
            return {'CANCELLED'}

        if self.target_obj.get("dbim_is_moving_anchor", False):
            return {'CANCELLED'}
        self.target_obj["dbim_is_moving_anchor"] = True

        self.initial_loc = tuple(self.target_obj.ifc_StartPoint) if self.anchor_index == 0 else tuple(self.target_obj.ifc_EndPoint)
        self.initial_z = self.initial_loc[2]
        self.snap_point_3d = None

        # Add visual feedback handler
        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

        self._state = 0
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if not getattr(self, 'target_obj', None) or self.target_obj.name not in bpy.data.objects:
            self.cleanup(context)
            return {'FINISHED'}

        if self._state == 0:
            if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
                self._state = 1
            return {'PASS_THROUGH'}

        if event.type == 'MOUSEMOVE':
            region = context.region
            rv3d = context.region_data
            coord = (event.mouse_region_x, event.mouse_region_y)
            
            view_vector = region_2d_to_vector_3d(region, rv3d, coord)
            ray_origin = region_2d_to_origin_3d(region, rv3d, coord)
            
            # Base Plane intersection Z = initial_z
            if abs(view_vector.z) > 1e-6:
                t = (self.initial_z - ray_origin.z) / view_vector.z
                loc = ray_origin + view_vector * t
            else:
                loc = mathutils.Vector(self.initial_loc)
                
            stationary_pt = self.target_obj.ifc_EndPoint if self.anchor_index == 0 else self.target_obj.ifc_StartPoint
            stationary_pt = mathutils.Vector(stationary_pt)

            self.snap_point_3d = None
            snapped = False
            
            # 1. Angle Snap (Ctrl)
            if event.ctrl:
                delta = loc - stationary_pt
                angle = math.atan2(delta.y, delta.x)
                # Snap to 15 degree increments (pi/12)
                snap_angle = round(angle / (math.pi / 12)) * (math.pi / 12)
                length = delta.xy.length
                loc.x = stationary_pt.x + length * math.cos(snap_angle)
                loc.y = stationary_pt.y + length * math.sin(snap_angle)
                snapped = True
                # No orange circle for angle snap, but we could draw guidelines later

            # 2. Blender-like Custom Snapping
            if context.scene.tool_settings.use_snap and not snapped:
                snap_elements = context.scene.tool_settings.snap_elements
                closest_dist = 20.0 # snap threshold in pixels
                closest_point = None
                
                # A. Prioritize DBIM Endpoints (VERTEX snapping behavior)
                if 'VERTEX' in snap_elements:
                    for obj in context.scene.objects:
                        if getattr(obj, "is_IfcWall", False) or getattr(obj, "is_IfcGridAxis", False):
                            if hasattr(obj, "ifc_StartPoint"):
                                sp = mathutils.Vector(obj.ifc_StartPoint)
                                sp_2d = location_3d_to_region_2d(region, rv3d, sp)
                                if sp_2d:
                                    dist = (sp_2d - mathutils.Vector(coord)).length
                                    if dist < closest_dist and (obj != self.target_obj or self.anchor_index != 0):
                                        closest_dist = dist
                                        closest_point = sp
                            
                            if hasattr(obj, "ifc_EndPoint"):
                                ep = mathutils.Vector(obj.ifc_EndPoint)
                                ep_2d = location_3d_to_region_2d(region, rv3d, ep)
                                if ep_2d:
                                    dist = (ep_2d - mathutils.Vector(coord)).length
                                    if dist < closest_dist and (obj != self.target_obj or self.anchor_index != 1):
                                        closest_dist = dist
                                        closest_point = ep

                # B. Fallback to Raycast for arbitrary scene meshes
                if closest_point:
                    loc.x = closest_point.x
                    loc.y = closest_point.y
                    self.snap_point_3d = closest_point
                else:
                    hit, hit_loc, normal, index, hit_obj, matrix = context.scene.ray_cast(context.view_layer.depsgraph, ray_origin, view_vector)
                    if hit:
                        # Depending on snap_elements, we could find the nearest vertex of the hit polygon.
                        # For now, we simulate FACE snapping by snapping to the exact ray hit location.
                        # But we could easily extract the nearest vertex here if needed.
                        loc.x = hit_loc.x
                        loc.y = hit_loc.y
                        
                        # Only show orange circle if snapping to VERTEX or EDGE is requested and we hit something
                        if 'VERTEX' in snap_elements or 'EDGE' in snap_elements or 'FACE' in snap_elements:
                            self.snap_point_3d = hit_loc
                        
            # APPLY RESULT (Force Z lock)
            if self.anchor_index == 0:
                self.target_obj.ifc_StartPoint = (loc.x, loc.y, self.initial_z)
            else:
                self.target_obj.ifc_EndPoint = (loc.x, loc.y, self.initial_z)
                
            self.target_obj.update_tag()

        elif event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'ESC', 'RET'} and event.value == 'PRESS':
            if event.type in {'RIGHTMOUSE', 'ESC'}:
                # Cancel
                if self.anchor_index == 0:
                    self.target_obj.ifc_StartPoint = self.initial_loc
                else:
                    self.target_obj.ifc_EndPoint = self.initial_loc
                self.target_obj.update_tag()
            
            self.cleanup(context)
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def cleanup(self, context):
        if getattr(self, 'target_obj', None):
            self.target_obj["dbim_is_moving_anchor"] = False
        if self._handle:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self._handle = None
            
        context.area.tag_redraw()

    def draw_callback_px(self, self_ref, context):
        if not self_ref.snap_point_3d:
            return

        region = context.region
        rv3d = context.region_data
        pos_2d = location_3d_to_region_2d(region, rv3d, self_ref.snap_point_3d)
        
        if not pos_2d:
            return

        shader = get_2d_shader()
        
        segments = 16
        radius = 7.0
        coords = []
        for i in range(segments):
            angle = (i * 2 * math.pi) / segments
            coords.append((pos_2d.x + math.cos(angle) * radius, pos_2d.y + math.sin(angle) * radius))
            angle_next = ((i + 1) * 2 * math.pi) / segments
            coords.append((pos_2d.x + math.cos(angle_next) * radius, pos_2d.y + math.sin(angle_next) * radius))

        # Add an inner crosshair for more "Blender-like" feel
        coords.append((pos_2d.x - radius, pos_2d.y))
        coords.append((pos_2d.x + radius, pos_2d.y))
        coords.append((pos_2d.x, pos_2d.y - radius))
        coords.append((pos_2d.x, pos_2d.y + radius))

        batch = batch_for_shader(shader, 'LINES', {"pos": coords})
        
        shader.bind()
        shader.uniform_float("color", (1.0, 0.5, 0.0, 1.0)) # Blender Orange
        
        # In modern Blender, gpu.state is used for line width
        gpu.state.line_width_set(2.0)
        batch.draw(shader)
        gpu.state.line_width_set(1.0)
