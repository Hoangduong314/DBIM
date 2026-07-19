import bpy
import mathutils

def update_wall_geometry(self, context):
    if not getattr(self, "is_IfcWall", False):
        return
        
    from ..core import wall_builder
    
    p1 = mathutils.Vector(self.ifc_StartPoint)
    p2 = mathutils.Vector(self.ifc_EndPoint)
    
    # Ignore if too close
    if (p2 - p1).length < 0.01:
        return

    # Get the type this wall is using (or fallback to active)
    wall_type = None
    if self.ifc_TypeName:
        wall_type = next((t for t in context.scene.ifc_WallTypes if t.name == self.ifc_TypeName), None)
    
    if not wall_type:
        wall_type = get_active_wall_type(context.scene)
        
    height = self.ifc_Height if self.ifc_Height > 0 else wall_type.default_height
    layers = wall_type.layers
    
    if len(layers) == 0:
        return
        
    # Build new mesh
    new_mesh_obj = wall_builder.create_wall_mesh([p1, p2], height, layers)
    if new_mesh_obj:
        old_mesh = self.data
        self.data = new_mesh_obj.data
        
        # Clean up the temporary object
        bpy.data.objects.remove(new_mesh_obj)
        
        # Clean up old mesh if no users
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)

def update_walls_of_type(self, context):
    # 'self' might be a layer or the type itself
    # We need to find the type name
    type_name = getattr(self, "name", "")
    
    # If self is a layer, we can't easily find its parent type name from the property group directly.
    # Instead, we just update ALL walls that match the currently selected type, or we could just 
    # force an update on all walls that have a matching type name if we find the type.
    # For simplicity, let's update all walls that use the active wall type (since the user is editing it).
    
    active_type = get_active_wall_type(context.scene)
    if not active_type: return
    
    for obj in context.scene.objects:
        if getattr(obj, "is_IfcWall", False) and getattr(obj, "ifc_TypeName", "") == active_type.name:
            # Trigger update
            # We can't call update_wall_geometry directly easily since it expects self = obj
            # But we can just set a property to trigger it, or call it manually
            update_wall_geometry(obj, context)

class IfcWallLayerItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name="Layer Name",
        default="Layer"
    )
    thickness: bpy.props.FloatProperty(
        name="Thickness",
        description="Thickness of this wall layer",
        default=0.1,
        min=0.001,
        unit='LENGTH',
        update=update_walls_of_type
    )
    material: bpy.props.PointerProperty(
        name="Material",
        type=bpy.types.Material
    )

class IfcWallTypeProps(bpy.types.PropertyGroup):
    # Dummy annotation so auto_load.py knows this class depends on IfcWallLayerItem
    _dependency: IfcWallLayerItem
    
    name: bpy.props.StringProperty(name="Type Name", default="New Wall Type")
    is_editing_type: bpy.props.BoolProperty(name="Edit Type", default=False)
    
    layers: bpy.props.CollectionProperty(type=IfcWallLayerItem)
    active_layer_index: bpy.props.IntProperty(name="Active Layer Index", default=0)
    
    default_height: bpy.props.FloatProperty(
        name="Default Height",
        description="Default height when drawing a new wall",
        default=3.0,
        min=0.1,
        unit='LENGTH',
        update=update_walls_of_type
    )

def get_active_wall_type(scene, create_if_empty=True):
    if len(scene.ifc_WallTypes) == 0:
        if not create_if_empty:
            return None
        new_type = scene.ifc_WallTypes.add()
        new_type.name = "Basic Wall"
        layer = new_type.layers.add()
        layer.name = "Structure"
        layer.thickness = 0.2
        scene.ifc_WallTypeIndex = 0
        return new_type
    
    idx = scene.ifc_WallTypeIndex
    if idx < 0 or idx >= len(scene.ifc_WallTypes):
        scene.ifc_WallTypeIndex = 0
        idx = 0
    return scene.ifc_WallTypes[idx]

def register():
    bpy.types.Scene.ifc_WallTypes = bpy.props.CollectionProperty(type=IfcWallTypeProps)
    bpy.types.Scene.ifc_WallTypeIndex = bpy.props.IntProperty(name="Active Wall Type", default=0)
    bpy.types.Object.is_IfcWall = bpy.props.BoolProperty(default=False)
    bpy.types.Object.ifc_TypeName = bpy.props.StringProperty(name="Wall Type Name", default="")
    bpy.types.Object.ifc_Height = bpy.props.FloatProperty(name="Height", default=3.0, update=update_wall_geometry)

def unregister():
    if hasattr(bpy.types.Object, "ifc_Height"):
        del bpy.types.Object.ifc_Height
    if hasattr(bpy.types.Object, "ifc_TypeName"):
        del bpy.types.Object.ifc_TypeName
    if hasattr(bpy.types.Object, "is_IfcWall"):
        del bpy.types.Object.is_IfcWall
    if hasattr(bpy.types.Scene, "ifc_WallTypeIndex"):
        del bpy.types.Scene.ifc_WallTypeIndex
    if hasattr(bpy.types.Scene, "ifc_WallTypes"):
        del bpy.types.Scene.ifc_WallTypes

