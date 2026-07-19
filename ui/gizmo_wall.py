import bpy
import mathutils

def get_direction_matrix(obj):
    p1 = mathutils.Vector(obj.ifc_StartPoint)
    p2 = mathutils.Vector(obj.ifc_EndPoint)
    diff = p2 - p1
    if diff.length < 0.001:
        direction = mathutils.Vector((1, 0, 0))
    else:
        direction = diff.normalized()
    return direction.to_track_quat('X', 'Z').to_matrix().to_4x4()

class DBIM_GGT_wall_endpoints(bpy.types.GizmoGroup):
    bl_idname = "DBIM_GGT_wall_endpoints"
    bl_label = "Wall Endpoints"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.select_get() and getattr(obj, "is_IfcWall", False)

    def setup(self, context):
        def get_p1():
            obj = bpy.context.active_object
            if obj and getattr(obj, "is_IfcWall", False):
                return obj.ifc_StartPoint
            return (0.0, 0.0, 0.0)

        def set_p1(value):
            obj = bpy.context.active_object
            if obj and getattr(obj, "is_IfcWall", False):
                obj.ifc_StartPoint = (value[0], value[1], obj.ifc_StartPoint[2])

        def get_p2():
            obj = bpy.context.active_object
            if obj and getattr(obj, "is_IfcWall", False):
                return obj.ifc_EndPoint
            return (0.0, 0.0, 0.0)

        def set_p2(value):
            obj = bpy.context.active_object
            if obj and getattr(obj, "is_IfcWall", False):
                obj.ifc_EndPoint = (value[0], value[1], obj.ifc_EndPoint[2])

        # Gizmo 1 for ifc_StartPoint
        m1 = self.gizmos.new("GIZMO_GT_move_3d")
        m1.target_set_handler("offset", get=get_p1, set=set_p1)
        m1.use_draw_modal = True
        if hasattr(m1, "draw_options"):
            m1.draw_options = {'X', 'Y', 'PLANE_XY'}
        
        # Color and visual style
        m1.alpha = 0.5
        m1.alpha_highlight = 1.0
        m1.scale_basis = 0.5
        self.p1_gizmo = m1

        # Gizmo 2 for ifc_EndPoint
        m2 = self.gizmos.new("GIZMO_GT_move_3d")
        m2.target_set_handler("offset", get=get_p2, set=set_p2)
        m2.use_draw_modal = True
        if hasattr(m2, "draw_options"):
            m2.draw_options = {'X', 'Y', 'PLANE_XY'}
        
        m2.alpha = 0.5
        m2.alpha_highlight = 1.0
        m2.scale_basis = 0.5
        self.p2_gizmo = m2

    def refresh(self, context):
        obj = context.active_object
        if obj and getattr(obj, "is_IfcWall", False):
            R = get_direction_matrix(obj)
            self.p1_gizmo.matrix_basis = obj.matrix_world.normalized()
            self.p1_gizmo.matrix_offset = R
            self.p2_gizmo.matrix_basis = obj.matrix_world.normalized()
            self.p2_gizmo.matrix_offset = R

def register():
    pass

def unregister():
    pass
