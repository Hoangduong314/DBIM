import bpy

class DBIM_OT_add_wall_layer(bpy.types.Operator):
    bl_idname = "dbim.add_wall_layer"
    bl_label = "Add Wall Layer"
    bl_description = "Add a new layer to the wall type"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ..props import props_wall
        wall_type = props_wall.get_active_wall_type(context.scene)
        new_layer = wall_type.layers.add()
        new_layer.name = f"Layer {len(wall_type.layers)}"
        new_layer.thickness = 0.1
        wall_type.active_layer_index = len(wall_type.layers) - 1
        return {'FINISHED'}

class DBIM_OT_remove_wall_layer(bpy.types.Operator):
    bl_idname = "dbim.remove_wall_layer"
    bl_label = "Remove Wall Layer"
    bl_description = "Remove the active layer from the wall type"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ..props import props_wall
        wall_type = props_wall.get_active_wall_type(context.scene)
        idx = wall_type.active_layer_index
        
        if len(wall_type.layers) > 0:
            wall_type.layers.remove(idx)
            if idx >= len(wall_type.layers):
                wall_type.active_layer_index = max(0, len(wall_type.layers) - 1)
                
        return {'FINISHED'}
