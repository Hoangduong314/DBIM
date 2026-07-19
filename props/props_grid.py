import bpy

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
    if not self.is_IfcGridAxis:
        return
        
    # Ensure mesh updates when points are changed
    if self.type == 'MESH':
        try:
            import mathutils
            import bmesh
            p1 = mathutils.Vector(self.ifc_StartPoint)
            p2 = mathutils.Vector(self.ifc_EndPoint)
            
            with open(r"G:\My Drive\Libraries\Blender\DBIM\debug.log", "a") as f:
                f.write(f"Updating grid points for {self.name}: p1={p1}, p2={p2}\n")
                
            if self.type == 'MESH' and self.data:
                bm = bmesh.new()
                
                diff = p2 - p1
                if diff.length > 0.001:
                    dir = diff.normalized()
                    perp = mathutils.Vector((-dir.y, dir.x, 0)) * 0.0001
                    v1 = bm.verts.new(p1 + perp)
                    v2 = bm.verts.new(p1 - perp)
                    v3 = bm.verts.new(p2 - perp)
                    v4 = bm.verts.new(p2 + perp)
                    bm.faces.new((v1, v2, v3, v4))
                else:
                    v1 = bm.verts.new(p1)
                    v2 = bm.verts.new(p2)
                    bm.edges.new((v1, v2))
                
                bm.to_mesh(self.data)
                bm.free()
                
                # Tag to force redraw
                if hasattr(self, 'update_tag'):
                    self.update_tag(refresh={'DATA'})
                    
        except Exception as e:
            with open(r"G:\My Drive\Libraries\Blender\DBIM\debug.log", "a") as f:
                f.write(f"ERROR: {str(e)}\n")

class DBIM_GridSettings(bpy.types.PropertyGroup):
    next_name: bpy.props.StringProperty(
        name="Next Grid Name",
        description="Name for the next grid to be drawn",
        default="1"
    )

def register():
    bpy.types.Object.is_IfcGridAxis = bpy.props.BoolProperty(
        name="Is DBIM Grid",
        description="True if this object is a DBIM Grid line",
        default=False
    )
    bpy.types.Object.ifc_AxisTag = bpy.props.StringProperty(
        name="Grid Name",
        description="Name/Label of the grid line",
        default=""
    )
    
    bpy.types.Scene.ifc_GridSettings = bpy.props.PointerProperty(type=DBIM_GridSettings)

def unregister():
    if hasattr(bpy.types.Object, "is_IfcGridAxis"):
        del bpy.types.Object.is_IfcGridAxis
    if hasattr(bpy.types.Object, "ifc_AxisTag"):
        del bpy.types.Object.ifc_AxisTag
    if hasattr(bpy.types.Scene, "ifc_GridSettings"):
        del bpy.types.Scene.ifc_GridSettings
