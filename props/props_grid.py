import bpy
import mathutils

def get_next_grid_name(current_name):
    # Auto increment letters or numbers
    if not current_name:
        return "1"
        
    # Try to increment as a number
    try:
        num = int(current_name)
        return str(num + 1)
    except ValueError:
        pass
        
    # Try to increment as a letter (e.g. A -> B, Z -> AA)
    if current_name.isalpha():
        # Simple single character increment
        if len(current_name) == 1:
            char = current_name.upper()
            if char == 'Z':
                return 'AA'
            return chr(ord(char) + 1)
            
    return current_name + "_new"

def update_grid_points(self, context):
    """
    Called when ifc_StartPoint or ifc_EndPoint changes.
    Updates the physical vertices or stroke points so the grid moves correctly.
    """
    if not self.is_IfcGridAxis:
        return
        
    try:
        if self.type == 'MESH':
            import bmesh
            if self.data:
                bm = bmesh.new()
                p1 = mathutils.Vector(self.ifc_StartPoint)
                p2 = mathutils.Vector(self.ifc_EndPoint)
                
                v1 = bm.verts.new(self.ifc_StartPoint)
                v2 = bm.verts.new(self.ifc_EndPoint)
                
                bm.to_mesh(self.data)
                bm.free()
                
                self.data.update()
        elif self.type == 'GREASEPENCIL':
            if len(self.data.layers) > 0 and len(self.data.layers[0].frames) > 0:
                frame = self.data.layers[0].frames[0]
                if len(frame.strokes) > 0:
                    stroke = frame.strokes[0]
                    if len(stroke.points) >= 2:
                        stroke.points[0].co = self.ifc_StartPoint
                        stroke.points[1].co = self.ifc_EndPoint
    except Exception as e:
        print(f"Error updating grid points: {e}")

def update_grid_name(self, context):
    """Update object name when ifc_AxisTag changes"""
    if self.is_IfcGridAxis:
        self.name = f"IfcGridAxis_{self.ifc_AxisTag}"

class DBIM_GridSettings(bpy.types.PropertyGroup):
    next_name: bpy.props.StringProperty(
        name="Next Grid Name",
        description="Name for the next grid to be drawn",
        default="1"
    )

def register():
    bpy.types.Object.is_IfcGridAxis = bpy.props.BoolProperty(
        name="Is IFC Grid Axis",
        default=False,
        description="Identifies this object as an IFC Grid Axis"
    )

    bpy.types.Object.ifc_AxisTag = bpy.props.StringProperty(
        name="Grid Name",
        default="1",
        update=update_grid_name
    )
    
    bpy.types.Scene.ifc_GridSettings = bpy.props.PointerProperty(type=DBIM_GridSettings)

def unregister():
    if hasattr(bpy.types.Object, "is_IfcGridAxis"):
        del bpy.types.Object.is_IfcGridAxis
    if hasattr(bpy.types.Object, "ifc_AxisTag"):
        del bpy.types.Object.ifc_AxisTag
    if hasattr(bpy.types.Scene, "ifc_GridSettings"):
        del bpy.types.Scene.ifc_GridSettings
