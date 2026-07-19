import bpy
import bmesh

def create_grid_mesh(p1, p2, name):
    """
    Generate a mesh object for a grid line.
    Creates a thin transparent quad so it is selectable and snappable,
    but visually invisible, allowing the GPU dashed line to show clearly.
    """
    import mathutils
    bm = bmesh.new()
    
    v1 = bm.verts.new(p1)
    v2 = bm.verts.new(p2)
    # No edges or faces so it doesn't draw any solid lines or selection outlines
    
    mesh = bpy.data.meshes.new(name=f"IfcGridAxis_{name}")
    bm.to_mesh(mesh)
    bm.free()
    
    # Create transparent material
    mat = bpy.data.materials.new(name=f"Transp_{name}")
    mat.use_nodes = True
    mat.blend_method = 'BLEND'
    mat.diffuse_color = (0, 0, 0, 0)
    mesh.materials.append(mat)
    
    obj = bpy.data.objects.new(f"IfcGridAxis_{name}", mesh)
    obj.display_type = 'SOLID'
    obj.show_transparent = True
    obj.color = (0, 0, 0, 0)
    
    return obj

