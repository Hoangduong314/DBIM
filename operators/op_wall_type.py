import bpy

class DBIM_OT_new_wall_type(bpy.types.Operator):
    bl_idname = "dbim.new_wall_type"
    bl_label = "New Wall Type"
    bl_description = "Create a new Wall Type"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        types = scene.ifc_WallTypes
        
        new_type = types.add()
        new_type.name = f"Wall Type {len(types)}"
        
        # Add default layer
        layer = new_type.layers.add()
        layer.name = "Structure"
        layer.thickness = 0.2
        
        # Set active to the new one
        scene.ifc_WallTypeIndex = len(types) - 1
        
        return {'FINISHED'}

class DBIM_OT_duplicate_wall_type(bpy.types.Operator):
    bl_idname = "dbim.duplicate_wall_type"
    bl_label = "Duplicate Wall Type"
    bl_description = "Duplicate the active Wall Type"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        types = scene.ifc_WallTypes
        
        from ..props.props_wall import get_active_wall_type
        active_type = get_active_wall_type(scene)
        
        new_type = types.add()
        new_type.name = f"{active_type.name} Copy"
        new_type.default_height = active_type.default_height
        
        for layer in active_type.layers:
            new_layer = new_type.layers.add()
            new_layer.name = layer.name
            new_layer.thickness = layer.thickness
            new_layer.material = layer.material
            
        # Set active to the new one
        scene.ifc_WallTypeIndex = len(types) - 1
        
        return {'FINISHED'}

class DBIM_OT_delete_wall_type(bpy.types.Operator):
    bl_idname = "dbim.delete_wall_type"
    bl_label = "Delete Wall Type"
    bl_description = "Delete the active Wall Type"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        types = scene.ifc_WallTypes
        idx = scene.ifc_WallTypeIndex
        
        # Keep at least one type
        if len(types) <= 1:
            self.report({'WARNING'}, "Cannot delete the last Wall Type")
            return {'CANCELLED'}
            
        types.remove(idx)
        
        # Adjust index
        if idx >= len(types):
            scene.ifc_WallTypeIndex = max(0, len(types) - 1)
            
        return {'FINISHED'}
