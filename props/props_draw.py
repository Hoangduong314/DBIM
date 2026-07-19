import bpy

class DBIM_DrawSettings(bpy.types.PropertyGroup):
    target_type: bpy.props.EnumProperty(
        name="Target",
        description="What to draw",
        items=[
            ('NONE', 'Select Category...', 'Choose what to draw', 'VIEW_PAN', 0),
            ('IfcWall', 'Wall', 'Draw an IfcWall', 'OUTLINER_OB_MESH', 1),
            ('IfcGridAxis', 'Grid Axis', 'Draw an IfcGridAxis', 'CON_TRACKTO', 2),
            ('IfcSlab', 'Slab', 'Draw an IfcSlab', 'MESH_PLANE', 3)
        ],
        default='NONE'
    )
    
    draw_system: bpy.props.EnumProperty(
        name="Draw System",
        description="Immediate or Boundary",
        items=[
            ('IMMEDIATE', 'Immediate', 'Create after 2 points', 'OUTLINER_OB_CURVE', 0),
            ('BOUNDARY', 'Boundary', 'Create after confirm', 'MESH_POLYGON', 1)
        ],
        default='IMMEDIATE'
    )
    
    draw_shape: bpy.props.EnumProperty(
        name="Shape",
        description="How to draw",
        items=[
            ('LINE', 'Line', 'Draw a single line', 'OUTLINER_OB_CURVE', 0),
            ('RECTANGLE', 'Rectangle', 'Draw a rectangle', 'MESH_CUBE', 1),
            ('CIRCLE', 'Circle', 'Draw a circle', 'MESH_CIRCLE', 2),
            ('PICK', 'Pick Line', 'Pick an edge and offset', 'EYEDROPPER', 3)
        ],
        default='LINE'
    )
    
    offset: bpy.props.FloatProperty(
        name="Offset",
        description="Offset distance for Pick Line or shapes",
        default=0.0,
        unit='LENGTH'
    )
    
    is_drawing: bpy.props.BoolProperty(
        name="Is Drawing",
        default=False
    )

def register():
    bpy.types.Scene.ifc_DrawSettings = bpy.props.PointerProperty(type=DBIM_DrawSettings)

def unregister():
    if hasattr(bpy.types.Scene, "ifc_DrawSettings"):
        del bpy.types.Scene.ifc_DrawSettings
