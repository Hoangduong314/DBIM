import bpy

class DBIM_PT_view_panel(bpy.types.Panel):
    bl_label = "DBIM Views"
    bl_idname = "DBIM_PT_view_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "DBIM View"

    def draw(self, context):
        layout = self.layout
        
        layout.operator("dbim.create_view", text="Create New View", icon='ADD')
        
        # List existing views
        views = [obj for obj in context.scene.objects if getattr(obj, "is_IfcAnnotation", False)]
        
        if views:
            layout.separator()
            layout.label(text="Project Views:")
            
            box = layout.box()
            for view in views:
                row = box.row()
                
                # Highlight active view
                if context.scene.camera == view:
                    row.label(text=view.ifc_Name, icon='CAMERA_DATA')
                else:
                    # Make a button to set it active
                    op = row.operator("dbim.set_active_view", text=view.ifc_Name, icon='CAMERA_DATA', emboss=False)
                    op.view_name = view.name
                    
        # If a view is selected, show its properties
        active_obj = context.active_object
        if active_obj and getattr(active_obj, "is_IfcAnnotation", False):
            layout.separator()
            layout.label(text="Active View Settings:")
            col = layout.column(align=True)
            col.prop(active_obj, "ifc_Name")
            col.prop(active_obj, "ifc_ViewType")
            col.prop(active_obj, "ifc_Scale")


class DBIM_OT_set_active_view(bpy.types.Operator):
    bl_idname = "dbim.set_active_view"
    bl_label = "Set Active View"
    bl_description = "Switch to this view"
    
    view_name: bpy.props.StringProperty()
    
    def execute(self, context):
        obj = context.scene.objects.get(self.view_name)
        if obj and obj.type == 'CAMERA':
            context.scene.camera = obj
            
            # Switch view to camera if in 3D view
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.spaces[0].region_3d.view_perspective = 'CAMERA'
                    break
                    
            # Also select it so properties show up
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            
        return {'FINISHED'}
