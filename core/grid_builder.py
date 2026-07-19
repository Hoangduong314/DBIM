import bpy
import bmesh

def create_grid_mesh(p1, p2, name):
    """
    Generate a mesh object for a grid line (single edge).
    Uses global GPU handler for dashed rendering.
    """
    bm = bmesh.new()
    
    # Create two vertices and an edge
    v1 = bm.verts.new(p1)
    v2 = bm.verts.new(p2)
    bm.edges.new((v1, v2))
    
    mesh = bpy.data.meshes.new(name=f"IfcGridAxis_{name}")
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new(f"IfcGridAxis_{name}", mesh)
    
    # Hide the mesh wireframe, display via GP instead
    obj.display_type = 'WIRE'
    
    return obj
