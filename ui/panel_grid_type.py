import bpy

class DBIM_PT_grid_type(bpy.types.Panel):
    bl_label = "DBIM Grid Type"
    bl_idname = "DBIM_PT_grid_type"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "DBIM"
    bl_order = 1
    bl_parent_id = "DBIM_PT_category_panel"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if hasattr(context.scene, "ifc_DrawSettings"):
            return context.scene.ifc_DrawSettings.target_type == 'IfcGridAxis'
        return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        grid_settings = scene.ifc_GridSettings

        layout.prop(grid_settings, "next_name")

class DBIM_PT_grid_object(bpy.types.Panel):
    bl_label = "Grid Data"
    bl_idname = "DBIM_PT_grid_object"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "DBIM"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and getattr(obj, "is_IfcGridAxis", False)

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        layout.prop(obj, "ifc_AxisTag")
        layout.prop(obj, "ifc_StartPoint")
        layout.prop(obj, "ifc_EndPoint")
