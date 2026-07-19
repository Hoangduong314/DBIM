import bpy

def update_ifc_points(self, context):
    if getattr(self, "is_IfcWall", False):
        from .props_wall import update_wall_geometry
        update_wall_geometry(self, context)
    elif getattr(self, "is_IfcGridAxis", False):
        from .props_grid import update_grid_points
        update_grid_points(self, context)

def update_view_scale(self, context):
    # When scale changes, update all grid GPs to adjust their dash sizes
    from ..core.grid_builder import update_grid_gp
    for obj in context.scene.objects:
        if getattr(obj, "is_IfcGridAxis", False):
            try:
                update_grid_gp(obj)
            except Exception:
                pass

scale_items = [
    ('10', "1:10", "1:10 Scale"),
    ('20', "1:20", "1:20 Scale"),
    ('50', "1:50", "1:50 Scale"),
    ('100', "1:100", "1:100 Scale"),
    ('200', "1:200", "1:200 Scale"),
    ('500', "1:500", "1:500 Scale"),
]

def register():
    bpy.types.Object.ifc_StartPoint = bpy.props.FloatVectorProperty(
        name="Start Point", size=3, update=update_ifc_points)
    bpy.types.Object.ifc_EndPoint = bpy.props.FloatVectorProperty(
        name="End Point", size=3, update=update_ifc_points)
        
    bpy.types.Scene.dbim_view_scale = bpy.props.EnumProperty(
        name="View Scale",
        description="Technical drawing scale for display",
        items=scale_items,
        default='100',
        update=update_view_scale
    )

def unregister():
    if hasattr(bpy.types.Scene, "dbim_view_scale"):
        del bpy.types.Scene.dbim_view_scale
    if hasattr(bpy.types.Object, "ifc_EndPoint"):
        del bpy.types.Object.ifc_EndPoint
    if hasattr(bpy.types.Object, "ifc_StartPoint"):
        del bpy.types.Object.ifc_StartPoint
