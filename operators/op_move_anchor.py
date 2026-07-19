import bpy
import math
import mathutils
from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d, location_3d_to_region_2d

class DBIM_OT_move_anchor(bpy.types.Operator):
    """Move Anchor (Click-Move-Click) with Custom Snapping"""
    bl_idname = "dbim.move_anchor"
    bl_label = "Move Anchor"
    bl_options = {'REGISTER', 'UNDO'}

    anchor_index: bpy.props.IntProperty(name="Anchor Index", default=0) # 0 for start, 1 for end
    
    def invoke(self, context, event):
        self.target_obj = context.active_object
        if not self.target_obj:
            return {'CANCELLED'}

        # Prevent multiple instances if user drags a drag-gizmo
        if self.target_obj.get("dbim_is_moving_anchor", False):
            return {'CANCELLED'}
        self.target_obj["dbim_is_moving_anchor"] = True

        self.initial_loc = tuple(self.target_obj.ifc_StartPoint) if self.anchor_index == 0 else tuple(self.target_obj.ifc_EndPoint)
        self.initial_z = self.initial_loc[2]

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if not getattr(self, 'target_obj', None) or self.target_obj.name not in bpy.data.objects:
            return {'FINISHED'}

        if event.type == 'MOUSEMOVE':
            region = context.region
            rv3d = context.region_data
            coord = (event.mouse_region_x, event.mouse_region_y)
            
            view_vector = region_2d_to_vector_3d(region, rv3d, coord)
            ray_origin = region_2d_to_origin_3d(region, rv3d, coord)
            
            # Plane intersection Z = initial_z
            if abs(view_vector.z) > 1e-6:
                t = (self.initial_z - ray_origin.z) / view_vector.z
                loc = ray_origin + view_vector * t
            else:
                loc = mathutils.Vector(self.initial_loc)
                
            stationary_pt = self.target_obj.ifc_EndPoint if self.anchor_index == 0 else self.target_obj.ifc_StartPoint
            stationary_pt = mathutils.Vector(stationary_pt)

            # Snap logic
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

            # 2. DBIM Endpoint Snap
            if context.scene.tool_settings.use_snap and not snapped:
                closest_dist = 20.0 # pixel radius
                closest_point = None
                
                # Check DBIM objects for endpoints
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
                
                if closest_point:
                    loc.x = closest_point.x
                    loc.y = closest_point.y
                else:
                    # Fallback to raycast for faces
                    hit, hit_loc, normal, index, hit_obj, matrix = context.scene.ray_cast(context.view_layer.depsgraph, ray_origin, view_vector)
                    if hit:
                        loc.x = hit_loc.x
                        loc.y = hit_loc.y
                        
            # Apply (lock Z)
            if self.anchor_index == 0:
                self.target_obj.ifc_StartPoint = (loc.x, loc.y, self.initial_z)
            else:
                self.target_obj.ifc_EndPoint = (loc.x, loc.y, self.initial_z)
                
            self.target_obj.update_tag()

        elif event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'ESC', 'RET'} and event.value == 'PRESS':
            self.target_obj["dbim_is_moving_anchor"] = False
            
            if event.type in {'RIGHTMOUSE', 'ESC'}:
                # Cancel
                if self.anchor_index == 0:
                    self.target_obj.ifc_StartPoint = self.initial_loc
                else:
                    self.target_obj.ifc_EndPoint = self.initial_loc
                self.target_obj.update_tag()
            return {'FINISHED'}

        return {'RUNNING_MODAL'}
