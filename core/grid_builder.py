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
    
    diff = p2 - p1
    if diff.length > 0.001:
        dir = diff.normalized()
        perp = mathutils.Vector((-dir.y, dir.x, 0)) * 0.05 # 5cm half-width for easy clicking
        
        v1 = bm.verts.new(p1 + perp)
        v2 = bm.verts.new(p1 - perp)
        v3 = bm.verts.new(p2 - perp)
        v4 = bm.verts.new(p2 + perp)
        bm.faces.new((v1, v2, v3, v4))
    else:
        v1 = bm.verts.new(p1)
        v2 = bm.verts.new(p2)
        bm.edges.new((v1, v2))
    
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

