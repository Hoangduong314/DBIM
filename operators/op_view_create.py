import bpy
import mathutils
import math

class DBIM_OT_create_view(bpy.types.Operator):
    bl_idname = "dbim.create_view"
    bl_label = "Create BIM View"
    bl_description = "Creates a new Camera acting as a BIM View"
    bl_options = {'REGISTER', 'UNDO'}

    view_type: bpy.props.EnumProperty(
        name="View Type",
        items=[
            ('3D', "3D View", "Perspective or Isometric 3D view"),
            ('PLAN', "Floor Plan", "View from top down"),
            ('SECTION', "Section", "Vertical cut view"),
            ('ELEVATION', "Elevation", "Side view without cut")
        ],
        default='3D'
    )

    view_name: bpy.props.StringProperty(
        name="View Name",
        default="Default 3D"
    )
    
    view_scale: bpy.props.IntProperty(
        name="Scale 1:",
        default=100,
        min=1
    )

    def invoke(self, context, event):
        # Update default name based on type
        if self.view_type == '3D':
            self.view_name = "Default 3D"
        elif self.view_type == 'PLAN':
            self.view_name = "Floor Plan Level 1"
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        # Create a new camera
        cam_data = bpy.data.cameras.new(name=self.view_name)
        
        if self.view_type == '3D':
            cam_data.type = 'PERSP'
            cam_data.lens = 35.0
            cam_data.clip_start = 0.1
            cam_data.clip_end = 1000.0
        else:
            cam_data.type = 'ORTHO'
            cam_data.ortho_scale = 10.0
            cam_data.clip_start = 0.1
            cam_data.clip_end = 100.0
        
        cam_obj = bpy.data.objects.new(self.view_name, cam_data)
        context.scene.collection.objects.link(cam_obj)
        
        if self.view_type == '3D':
            # Position for 3D View
            cam_obj.location = (15, -15, 12)
            cam_obj.rotation_euler = (math.radians(60), 0, math.radians(45))
        elif self.view_type == 'PLAN':
            # Position for Floor Plan
            cam_obj.location = (0, 0, 1.2)
            cam_obj.rotation_euler = (0, 0, 0)
        elif self.view_type in {'ELEVATION', 'SECTION'}:
            # Position looking from Front
            cam_obj.location = (0, -10, 0)
            cam_obj.rotation_euler = (math.radians(90), 0, 0)
        
        # Assign DBIM Properties
        cam_obj.is_IfcAnnotation = True
        cam_obj.ifc_Name = self.view_name
        cam_obj.ifc_ViewType = self.view_type
        cam_obj.ifc_Scale = self.view_scale
        
        # Select the new camera
        bpy.ops.object.select_all(action='DESELECT')
        cam_obj.select_set(True)
        context.view_layer.objects.active = cam_obj
        
        # Optionally make it the active scene camera
        context.scene.camera = cam_obj
        
        self.report({'INFO'}, f"Created View: {self.view_name} (1:{self.view_scale})")
        
        return {'FINISHED'}
