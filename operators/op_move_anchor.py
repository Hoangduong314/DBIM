import bpy
import mathutils
from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d

class DBIM_OT_move_anchor(bpy.types.Operator):
    """Move Anchor (Click-Move-Click)"""
    bl_idname = "dbim.move_anchor"
    bl_label = "Move Anchor"
    bl_options = {'REGISTER', 'UNDO'}

    anchor_index: bpy.props.IntProperty(name="Anchor Index", default=0) # 0 for start, 1 for end
    
    # Internal states
    initial_z = 0.0
    original_p1 = None
    original_p2 = None

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and (getattr(obj, "is_IfcWall", False) or getattr(obj, "is_IfcGridAxis", False))

    def invoke(self, context, event):
        obj = context.active_object
        self.original_p1 = mathutils.Vector(obj.ifc_StartPoint)
        self.original_p2 = mathutils.Vector(obj.ifc_EndPoint)
        
        if self.anchor_index == 0:
            self.initial_z = self.original_p1.z
        else:
            self.initial_z = self.original_p2.z

        context.window_manager.modal_handler_add(self)
        self.use_snap = context.scene.tool_settings.use_snap
        
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        obj = context.active_object
        if not obj:
            return {'CANCELLED'}
            
        context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            region = context.region
            rv3d = context.region_data
            coord = event.mouse_region_x, event.mouse_region_y
            
            view_vector = region_2d_to_vector_3d(region, rv3d, coord)
            ray_origin = region_2d_to_origin_3d(region, rv3d, coord)
            
            snap_point = None
            if self.use_snap:
                result, location, normal, index, hit_obj, matrix = context.scene.ray_cast(
                    context.view_layer.depsgraph, ray_origin, view_vector)
                
                if result:
                    # Chuyển về hệ tọa độ local của object
                    snap_point = obj.matrix_world.inverted() @ location
            
            if not snap_point:
                matrix_inv = obj.matrix_world.inverted()
                local_origin = matrix_inv @ ray_origin
                local_vector = (matrix_inv.to_3x3() @ view_vector).normalized()
                
                if abs(local_vector.z) > 1e-6:
                    t = (self.initial_z - local_origin.z) / local_vector.z
                    snap_point = local_origin + local_vector * t
                else:
                    snap_point = local_origin
                    
            # Enforce Z constraint
            snap_point.z = self.initial_z
            
            if self.anchor_index == 0:
                obj.ifc_StartPoint = snap_point
            else:
                obj.ifc_EndPoint = snap_point

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            return {'FINISHED'}
            
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            obj.ifc_StartPoint = self.original_p1
            obj.ifc_EndPoint = self.original_p2
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

classes = (
    DBIM_OT_move_anchor,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
