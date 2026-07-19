import bpy

def register():
    # Properties attached to Camera Objects
    bpy.types.Object.is_IfcAnnotation = bpy.props.BoolProperty(
        name="Is DBIM View",
        description="True if this camera acts as a DBIM View",
        default=False
    )
    
    bpy.types.Object.ifc_Name = bpy.props.StringProperty(
        name="View Name",
        description="Name of the DBIM View",
        default="New View"
    )
    
    bpy.types.Object.ifc_ViewType = bpy.props.EnumProperty(
        name="View Type",
        description="Type of BIM View",
        items=[
            ('PLAN', "Floor Plan", "View from top down"),
            ('SECTION', "Section", "Vertical cut view"),
            ('ELEVATION', "Elevation", "Side view without cut"),
            ('3D', "3D View", "Perspective or Isometric 3D view")
        ],
        default='PLAN'
    )
    
    bpy.types.Object.ifc_Scale = bpy.props.IntProperty(
        name="View Scale 1:",
        description="Scale factor (e.g. 100 for 1:100). Used for scaling annotations.",
        default=100,
        min=1,
        max=5000
    )

def unregister():
    if hasattr(bpy.types.Object, "is_IfcAnnotation"):
        del bpy.types.Object.is_IfcAnnotation
    if hasattr(bpy.types.Object, "ifc_Name"):
        del bpy.types.Object.ifc_Name
    if hasattr(bpy.types.Object, "ifc_ViewType"):
        del bpy.types.Object.ifc_ViewType
    if hasattr(bpy.types.Object, "ifc_Scale"):
        del bpy.types.Object.ifc_Scale
