import bpy

class DBIM_OT_edit_wall_type_dialog(bpy.types.Operator):
    bl_idname = "dbim.edit_wall_type_dialog"
    bl_label = "Type Properties"
    bl_options = {'REGISTER', 'UNDO'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=450)
        
    def draw(self, context):
        layout = self.layout
        from ..props.props_wall import get_active_wall_type
        wall_type = get_active_wall_type(context.scene)
        
        layout.prop(wall_type, "name", text="Type Name")
        layout.separator()
        
        layout.prop(wall_type, "default_height")
        
        layout.separator()
        layout.label(text="Wall Layers:")
        
        layout.template_list("DBIM_UL_wall_layers_v2", "dbim_wall_layers_list", wall_type, "layers", wall_type, "active_layer_index", rows=4)
        
        row = layout.row(align=True)
        row.operator("dbim.add_wall_layer", text="Add Layer", icon='ADD')
        row.operator("dbim.remove_wall_layer", text="Remove Layer", icon='REMOVE')
        
        if len(wall_type.layers) > 0:
            total_thickness = sum([layer.thickness for layer in wall_type.layers])
            layout.label(text=f"Total Thickness: {total_thickness:.3f} m")
            
    def execute(self, context):
        # Changes are made in real-time, so nothing strictly needed here.
        return {'FINISHED'}
