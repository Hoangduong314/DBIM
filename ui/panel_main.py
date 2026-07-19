import bpy

def draw_dbim_header(self, context):
    layout = self.layout
    scene = context.scene
    
    if not hasattr(scene, "ifc_DrawSettings"):
        return
        
    draw_settings = scene.ifc_DrawSettings
    
    layout.separator_spacer()
    layout.label(text="DBIM:", icon='MOD_BUILD')
    
    row = layout.row(align=True)
    target = draw_settings.target_type
    
    op = row.operator("dbim.start_tool", text="", icon='CANCEL', depress=(target == 'NONE'))
    op.target = 'NONE'
    op.shape = ''
    
    op = row.operator("dbim.start_tool", text="Wall", depress=(target == 'IfcWall'))
    op.target = 'IfcWall'
    op.shape = ''
    
    op = row.operator("dbim.start_tool", text="Grid", depress=(target == 'IfcGridAxis'))
    op.target = 'IfcGridAxis'
    op.shape = ''
    
    op = row.operator("dbim.start_tool", text="Slab", depress=(target == 'IfcSlab'))
    op.target = 'IfcSlab'
    op.shape = ''
    
    if target != 'NONE':
        layout.separator()
        row = layout.row(align=True)
        is_drawing = draw_settings.is_drawing
        shape = draw_settings.draw_shape
        
        op = row.operator("dbim.start_tool", text="", icon='OUTLINER_OB_CURVE', depress=(is_drawing and shape == 'LINE'))
        op.shape = 'LINE'
        
        if target in ['IfcWall', 'IfcSlab']:
            op = row.operator("dbim.start_tool", text="", icon='MESH_CUBE', depress=(is_drawing and shape == 'RECTANGLE'))
            op.shape = 'RECTANGLE'
            
            op = row.operator("dbim.start_tool", text="", icon='MESH_CIRCLE', depress=(is_drawing and shape == 'CIRCLE'))
            op.shape = 'CIRCLE'
            
        if target in ['IfcWall', 'IfcGridAxis']:
            op = row.operator("dbim.start_tool", text="", icon='EYEDROPPER', depress=(is_drawing and shape == 'PICK'))
            op.shape = 'PICK'
            
        if shape == 'PICK' and target in ['IfcWall', 'IfcGridAxis']:
            layout.separator()
            row = layout.row()
            row.prop(draw_settings, "offset", text="Offset")
            
        if is_drawing and draw_settings.draw_system == 'BOUNDARY':
            layout.separator()
            layout.label(text="Press ENTER to Confirm", icon='CHECKMARK')

classes = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_HT_tool_header.append(draw_dbim_header)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_HT_tool_header.remove(draw_dbim_header)
