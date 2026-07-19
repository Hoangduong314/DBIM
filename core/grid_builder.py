import bpy
import bmesh

def create_grid_mesh(p1, p2, name):
    """
    Generate a mesh object for a grid line (vertices only, no edge).
    Uses global GPU handler for dashed rendering to avoid solid edge overlap.
    """
    bm = bmesh.new()
    
    # Create two vertices (no edge so it doesn't draw a solid line)
    v1 = bm.verts.new(p1)
    v2 = bm.verts.new(p2)
    
    mesh = bpy.data.meshes.new(name=f"IfcGridAxis_{name}")
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new(f"IfcGridAxis_{name}", mesh)
    
    # Hide the mesh wireframe, display via GP instead
    obj.display_type = 'WIRE'
    
    return obj
