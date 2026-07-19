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
    """Move Anchor (Custom Snap Engine)"""
    bl_idname = "dbim.move_anchor"
    bl_label = "Move Anchor"
    bl_options = {'REGISTER', 'UNDO'}

    anchor_index: bpy.props.IntProperty(name="Anchor Index", default=0)
    
    _handle = None
    snap_point_3d = None
    extend_mode = False

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
        
        self.extend_mode = False
        self.snap_point_3d = None
        self._state = 0 # 0: waiting for first release, 1: transforming

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

        if event.type == 'TAB' and event.value == 'PRESS':
            self.extend_mode = not self.extend_mode
            context.area.tag_redraw()
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
                            sp = mathutils.Vector(obj.ifc_StartPoint)
                            sp_2d = location_3d_to_region_2d(region, rv3d, sp)
                            if sp_2d and (sp_2d - mathutils.Vector(coord)).length < closest_dist:
                                if obj != self.target_obj or self.anchor_index != 0:
                                    closest_dist = (sp_2d - mathutils.Vector(coord)).length
                                    closest_point = sp
                        if hasattr(obj, "ifc_EndPoint"):
                            ep = mathutils.Vector(obj.ifc_EndPoint)
                            ep_2d = location_3d_to_region_2d(region, rv3d, ep)
                            if ep_2d and (ep_2d - mathutils.Vector(coord)).length < closest_dist:
                                if obj != self.target_obj or self.anchor_index != 1:
                                    closest_dist = (ep_2d - mathutils.Vector(coord)).length
                                    closest_point = ep
                                    
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
                            closest_point = hit_loc # Fallback to face

                if closest_point:
                    loc = closest_point
                    self.snap_point_3d = closest_point

            # Apply constraints
            if self.extend_mode:
                # Project loc onto grid line
                v = loc - self.grid_origin
                proj_len = v.dot(self.grid_dir)
                loc = self.grid_origin + self.grid_dir * proj_len

            # APPLY RESULT
            if self.anchor_index == 0:
                self.target_obj.ifc_StartPoint = (loc.x, loc.y, self.initial_z)
            else:
                self.target_obj.ifc_EndPoint = (loc.x, loc.y, self.initial_z)
            self.target_obj.update_tag()
            context.area.tag_redraw()

        elif event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'ESC', 'RET'} and event.value == 'PRESS':
            if event.type in {'RIGHTMOUSE', 'ESC'}:
                if self.anchor_index == 0: self.target_obj.ifc_StartPoint = self.initial_loc
                else: self.target_obj.ifc_EndPoint = self.initial_loc
                self.target_obj.update_tag()
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
                
        # 2. Draw Extension Tracking Line if extend_mode is active
        if getattr(self_ref, 'extend_mode', False):
            p1 = self_ref.grid_origin - self_ref.grid_dir * 1000
            p2 = self_ref.grid_origin + self_ref.grid_dir * 1000
            p1_2d = location_3d_to_region_2d(context.region, context.region_data, p1)
            p2_2d = location_3d_to_region_2d(context.region, context.region_data, p2)
            if p1_2d and p2_2d:
                batch = batch_for_shader(shader, 'LINES', {"pos": [p1_2d, p2_2d]})
                shader.uniform_float("color", (1.0, 0.2, 0.2, 0.6))
                gpu.state.line_width_set(1.5)
                batch.draw(shader)
                gpu.state.line_width_set(1.0)
