import bpy

class DBIM_UL_wall_layers_v2(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name)

class DBIM_UL_wall_types_v2(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name)

class DBIM_PT_wall_type_panel(bpy.types.Panel):
    bl_label = "DBIM Wall Type"
    bl_idname = "DBIM_PT_wall_type_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "DBIM"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        if hasattr(context.scene, "ifc_DrawSettings"):
            return context.scene.ifc_DrawSettings.target_type == 'IfcWall'
        return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        try:
            from ..props.props_wall import get_active_wall_type
            wall_type = get_active_wall_type(scene, create_if_empty=False)
            
            if not wall_type:
                layout.label(text="No Wall Types exist.")
                layout.operator("dbim.new_wall_type", text="Initialize Wall Types", icon='ADD')
                return
            
            # --- Type Selection ---
            layout.label(text="Select Type:")
            layout.template_list("DBIM_UL_wall_types_v2", "dbim_wall_types_list", scene, "ifc_WallTypes", scene, "ifc_WallTypeIndex", rows=3)
            
            row = layout.row(align=True)
            row.operator("dbim.new_wall_type", text="New", icon='ADD')
            row.operator("dbim.duplicate_wall_type", text="Duplicate", icon='DUPLICATE')
            row.operator("dbim.delete_wall_type", text="Delete", icon='REMOVE')
            
            # --- Rename ---
            layout.prop(wall_type, "name", text="Rename")
            
            layout.separator()
            
            # --- Edit Type Dialog ---
            layout.operator("dbim.edit_wall_type_dialog", text="Edit Type", icon='PREFERENCES')
        except Exception as e:
            import traceback
            for line in traceback.format_exc().split('\n'):
                layout.label(text=line, icon='ERROR')
