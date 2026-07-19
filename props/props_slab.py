import bpy

def register():
    bpy.types.Object.is_IfcSlab = bpy.props.BoolProperty(default=False)
    bpy.types.Object.ifc_Thickness = bpy.props.FloatProperty(name="Thickness", default=0.2, unit='LENGTH')

def unregister():
    if hasattr(bpy.types.Object, "is_IfcSlab"):
        del bpy.types.Object.is_IfcSlab
    if hasattr(bpy.types.Object, "ifc_Thickness"):
        del bpy.types.Object.ifc_Thickness
