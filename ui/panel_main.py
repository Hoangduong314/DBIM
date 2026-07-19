import bpy

class DBIM_PT_category_panel(bpy.types.Panel):
    bl_label = "DBIM Tools"
    bl_idname = "DBIM_PT_category_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "DBIM"
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        if hasattr(scene, "dbim_view_scale"):
            row = layout.row()
            row.prop(scene, "dbim_view_scale", text="Scale")
            layout.separator()
            
        if hasattr(scene, "ifc_DrawSettings"):
            draw_settings = scene.ifc_DrawSettings
            
            cat_box = layout.box()
            cat_box.label(text="Category", icon='OUTLINER_COLLECTION')
            target = draw_settings.target_type
            row = cat_box.row(align=True)
            op = row.operator("dbim.start_tool", text="None", depress=(target == 'NONE'))
            op.target = 'NONE'
            op.shape = ''
            
            op = row.operator("dbim.start_tool", text="Wall", depress=(target == 'IfcWall'))
            op.target = 'IfcWall'
            op.shape = ''
            
            op = row.operator("dbim.start_tool", text="Grid Axis", depress=(target == 'IfcGridAxis'))
            op.target = 'IfcGridAxis'
            op.shape = ''
            
            op = row.operator("dbim.start_tool", text="Slab", depress=(target == 'IfcSlab'))
            op.target = 'IfcSlab'
            op.shape = ''
            
        obj = context.active_object
        if obj:
            if getattr(obj, "is_IfcWall", False):
                layout.separator()
                box = layout.box()
                box.label(text="Active: IfcWall", icon='INFO')
            elif getattr(obj, "is_IfcGridAxis", False):
                layout.separator()
                box = layout.box()
                box.label(text="Active: IfcGridAxis", icon='INFO')
            elif getattr(obj, "is_IfcAnnotation", False):
                layout.separator()
                box = layout.box()
                box.label(text="Active: IfcAnnotation", icon='INFO')
            elif getattr(obj, "is_IfcSlab", False):
                layout.separator()
                box = layout.box()
                box.label(text="Active: IfcSlab", icon='INFO')

class DBIM_PT_draw_mode_panel(bpy.types.Panel):
    bl_label = "Draw Mode"
    bl_idname = "DBIM_PT_draw_mode_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "DBIM"
    bl_order = 2

    @classmethod
    def poll(cls, context):
        if hasattr(context.scene, "ifc_DrawSettings"):
            return context.scene.ifc_DrawSettings.target_type != 'NONE'
        return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        try:
            if hasattr(scene, "ifc_DrawSettings"):
                draw_settings = scene.ifc_DrawSettings
                
                box = layout.box()
                
                row = box.row(align=True)
                
                is_drawing = draw_settings.is_drawing
                shape = draw_settings.draw_shape
                target = draw_settings.target_type
                
                # Line is available for all tools
                op = row.operator("dbim.start_tool", text="Line", icon='OUTLINER_OB_CURVE', depress=(is_drawing and shape == 'LINE'))
                op.shape = 'LINE'
                
                # Rect and Circle are only for Wall and Slab
                if target in ['IfcWall', 'IfcSlab']:
                    op = row.operator("dbim.start_tool", text="Rect", icon='MESH_CUBE', depress=(is_drawing and shape == 'RECTANGLE'))
                    op.shape = 'RECTANGLE'
                    
                    op = row.operator("dbim.start_tool", text="Circle", icon='MESH_CIRCLE', depress=(is_drawing and shape == 'CIRCLE'))
                    op.shape = 'CIRCLE'
                
                # Pick is for Wall and Grid Axis
                if target in ['IfcWall', 'IfcGridAxis']:
                    op = row.operator("dbim.start_tool", text="Pick", icon='EYEDROPPER', depress=(is_drawing and shape == 'PICK'))
                    op.shape = 'PICK'
                
                if shape == 'PICK' and target in ['IfcWall', 'IfcGridAxis']:
                    box.prop(draw_settings, "offset")
                    
                if is_drawing and draw_settings.draw_system == 'BOUNDARY':
                    layout.separator()
                    info = layout.box()
                    info.label(text="Boundary Mode Active", icon='INFO')
                    info.label(text="Press ENTER to Confirm", icon='CHECKMARK')
                    info.label(text="Press ESC to Cancel", icon='CANCEL')
        except Exception as e:
            import traceback
            for line in traceback.format_exc().split('\n'):
                layout.label(text=line, icon='ERROR')
