import bpy

def update_ifc_points(self, context):
    if getattr(self, "is_IfcWall", False):
        from .props_wall import update_wall_geometry
        update_wall_geometry(self, context)
    elif getattr(self, "is_IfcGridAxis", False):
        from .props_grid import update_grid_points
        update_grid_points(self, context)

def register():
    bpy.types.Object.ifc_StartPoint = bpy.props.FloatVectorProperty(
        name="Start Point", size=3, update=update_ifc_points)
    bpy.types.Object.ifc_EndPoint = bpy.props.FloatVectorProperty(
        name="End Point", size=3, update=update_ifc_points)

def unregister():
    if hasattr(bpy.types.Object, "ifc_EndPoint"):
        del bpy.types.Object.ifc_EndPoint
    if hasattr(bpy.types.Object, "ifc_StartPoint"):
        del bpy.types.Object.ifc_StartPoint
