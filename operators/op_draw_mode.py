import bpy
import bmesh
import mathutils
import math
import gpu
from gpu_extras.batch import batch_for_shader
from ..core import wall_builder, grid_builder
from ..props import props_grid

def draw_callback_px(self, context):
    if not hasattr(self, 'drawn_points'):
        return
        
    scene = context.scene
    settings = scene.ifc_DrawSettings
    
    points_3d = list(self.drawn_points)
    
    if self.mouse_pos_3d:
        if settings.draw_shape == 'LINE':
            if len(points_3d) > 0:
                points_3d.append(self.mouse_pos_3d)
                
        elif settings.draw_shape == 'RECTANGLE':
            if len(points_3d) > 0:
                p1 = points_3d[0]
                p3 = self.mouse_pos_3d
                p2 = mathutils.Vector((p3.x, p1.y, p1.z))
                p4 = mathutils.Vector((p1.x, p3.y, p1.z))
                points_3d = [p1, p2, p3, p4, p1]
                
        elif settings.draw_shape == 'CIRCLE':
            if len(points_3d) > 0:
                center = points_3d[0]
                radius = (self.mouse_pos_3d - center).length
                points_3d = []
                segments = 32
                for i in range(segments + 1):
                    angle = (i / segments) * 2 * math.pi
                    x = center.x + radius * math.cos(angle)
                    y = center.y + radius * math.sin(angle)
                    points_3d.append(mathutils.Vector((x, y, center.z)))

    if len(points_3d) > 1:
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        
        # In boundary mode, optionally draw dashed closing line to first point
        # But for now, just draw the strip
        batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": points_3d})
        
        gpu.state.line_width_set(2.0)
        gpu.state.blend_set('ALPHA')
        shader.bind()
        if settings.target_type == 'IfcWall':
            shader.uniform_float("color", (0.8, 0.2, 0.2, 1.0))
        elif settings.target_type == 'IfcSlab':
            shader.uniform_float("color", (0.2, 0.2, 0.8, 1.0))
        else:
            shader.uniform_float("color", (0.2, 0.8, 0.2, 1.0))
        batch.draw(shader)
        gpu.state.blend_set('NONE')


class DBIM_OT_draw_mode(bpy.types.Operator):
    bl_idname = "dbim.draw_mode"
    bl_label = "Draw Mode"
    bl_description = "Unified Draw Mode for all DBIM elements"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def modal(self, context, event):
        context.area.tag_redraw()
        
        scene = context.scene
        if not hasattr(scene, "ifc_DrawSettings"):
            return {'CANCELLED'}
            
        settings = scene.ifc_DrawSettings
        
        # If user turned off is_drawing from UI, finish
        if not settings.is_drawing:
            self.finish(context)
            return {'FINISHED'}

        if event.type == 'MOUSEMOVE':
            self.update_mouse_pos(context, event)

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            # Check if mouse is inside the 3D Viewport window (not over UI panels)
            if not (0 <= event.mouse_region_x <= context.region.width and 0 <= event.mouse_region_y <= context.region.height):
                return {'PASS_THROUGH'}
                
            if settings.draw_shape == 'PICK':
                self.handle_pick_line(context, event)
            else:
                self.handle_draw(context)
                
            return {'RUNNING_MODAL'}

        elif event.type == 'RET' and event.value == 'PRESS':
            if settings.draw_system == 'BOUNDARY':
                self.handle_confirm(context)
            else:
                self.finish(context)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            self.finish(context)
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def handle_confirm(self, context):
        if len(self.drawn_points) >= 3:
            # Connect last point to first point if not already connected
            if (self.drawn_points[-1] - self.drawn_points[0]).length > 0.001:
                self.drawn_points.append(self.drawn_points[0])
            self.dispatch_creation(context, self.drawn_points)
            self.drawn_points = []
            
        context.scene.ifc_DrawSettings.is_drawing = False
        self.finish(context)

    def handle_draw(self, context):
        if not self.mouse_pos_3d:
            return
            
        settings = context.scene.ifc_DrawSettings
        
        self.drawn_points.append(self.mouse_pos_3d)
        
        if settings.draw_shape == 'LINE':
            if settings.draw_system == 'IMMEDIATE' and len(self.drawn_points) == 2:
                self.dispatch_creation(context, self.drawn_points)
                self.drawn_points = []
        
        elif settings.draw_shape == 'RECTANGLE':
            if len(self.drawn_points) == 2:
                p1 = self.drawn_points[0]
                p3 = self.drawn_points[1]
                p2 = mathutils.Vector((p3.x, p1.y, p1.z))
                p4 = mathutils.Vector((p1.x, p3.y, p1.z))
                points = [p1, p2, p3, p4, p1]
                self.dispatch_creation(context, points)
                self.drawn_points = []
                if settings.draw_system == 'BOUNDARY':
                    # Rectangle automatically finishes even in boundary mode
                    self.handle_confirm(context)
                    
        elif settings.draw_shape == 'CIRCLE':
            if len(self.drawn_points) == 2:
                center = self.drawn_points[0]
                radius = (self.drawn_points[1] - center).length
                points = []
                segments = 32
                for i in range(segments + 1):
                    angle = (i / segments) * 2 * math.pi
                    x = center.x + radius * math.cos(angle)
                    y = center.y + radius * math.sin(angle)
                    points.append(mathutils.Vector((x, y, center.z)))
                self.dispatch_creation(context, points)
                self.drawn_points = []
                if settings.draw_system == 'BOUNDARY':
                    self.handle_confirm(context)

    def handle_pick_line(self, context, event):
        if hasattr(self, 'drawn_points') and len(self.drawn_points) == 2:
            self.dispatch_creation(context, self.drawn_points)
            self.drawn_points = []

    def get_pick_preview(self, context, event):
        region = context.region
        rv3d = context.region_data
        coord = event.mouse_region_x, event.mouse_region_y
        from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d
        
        view_vector = region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = region_2d_to_origin_3d(region, rv3d, coord)
        
        result, location, normal, index, obj, matrix = context.scene.ray_cast(
            context.view_layer.depsgraph, ray_origin, view_vector)
        
        if result and obj and obj.type == 'MESH':
            mesh = obj.data
            poly = mesh.polygons[index]
            closest_edge = None
            min_dist = float('inf')
            
            loc_local = obj.matrix_world.inverted() @ location
            
            for loop_idx in poly.loop_indices:
                edge_idx = mesh.loops[loop_idx].edge_index
                edge = mesh.edges[edge_idx]
                
                v1 = mesh.vertices[edge.vertices[0]].co
                v2 = mesh.vertices[edge.vertices[1]].co
                
                intersect_pt = mathutils.geometry.intersect_point_line(loc_local, v1, v2)[0]
                dist = (intersect_pt - loc_local).length
                
                if dist < min_dist:
                    min_dist = dist
                    closest_edge = edge
            
            if closest_edge:
                p1_local = mesh.vertices[closest_edge.vertices[0]].co
                p2_local = mesh.vertices[closest_edge.vertices[1]].co
                p1_world = obj.matrix_world @ p1_local
                p2_world = obj.matrix_world @ p2_local
                
                p1_2d = mathutils.Vector((p1_world.x, p1_world.y, 0))
                p2_2d = mathutils.Vector((p2_world.x, p2_world.y, 0))
                
                settings = context.scene.ifc_DrawSettings
                
                if (p2_2d - p1_2d).length > 0.001:
                    perp = mathutils.Vector((-(p2_2d.y - p1_2d.y), (p2_2d.x - p1_2d.x), 0)).normalized()
                    p1_offset = p1_2d + perp * settings.offset
                    p2_offset = p2_2d + perp * settings.offset
                    
                    return [p1_offset, p2_offset]
        return []

    def dispatch_creation(self, context, points):
        settings = context.scene.ifc_DrawSettings
        
        if settings.target_type == 'IfcWall':
            from ..props.props_wall import get_active_wall_type
            wall_type = get_active_wall_type(context.scene)
            obj = wall_builder.create_wall_mesh(points, wall_type.default_height, wall_type.layers)
            if obj:
                # Setup proper object properties
                obj.ifc_StartPoint = points[0]
                obj.ifc_EndPoint = points[-1]
                obj.ifc_Height = wall_type.default_height
                obj.is_IfcWall = True
                obj.ifc_TypeName = wall_type.name
                context.collection.objects.link(obj)
                self.select_object(context, obj)
                
        elif settings.target_type == 'IfcGridAxis':
            # Grids are usually drawn segment by segment
            for i in range(len(points) - 1):
                p1 = points[i]
                p2 = points[i+1]
                grid_name = context.scene.ifc_GridSettings.next_name
                obj = grid_builder.create_grid_mesh(p1, p2, grid_name)
                if obj:
                    obj.ifc_StartPoint = p1
                    obj.ifc_EndPoint = p2
                    obj.ifc_AxisTag = grid_name
                    obj.is_IfcGridAxis = True
                    obj.show_name = True
                    context.collection.objects.link(obj)
                    context.scene.ifc_GridSettings.next_name = props_grid.get_next_grid_name(grid_name)
                    self.select_object(context, obj)
                    
        elif settings.target_type == 'IfcSlab':
            if len(points) >= 3:
                mesh = bpy.data.meshes.new("Slab")
                obj = bpy.data.objects.new("Slab", mesh)
                
                bm = bmesh.new()
                bmesh_verts = []
                for p in points:
                    bmesh_verts.append(bm.verts.new(p))
                
                # Create a single face covering all points (assumes coplanar/ordered points)
                try:
                    bm.faces.new(bmesh_verts)
                except Exception:
                    pass
                    
                # Optionally solidify (extrude down)
                geom = bm.faces[:] + bm.verts[:] + bm.edges[:]
                res = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
                extruded_verts = [v for v in res['geom'] if isinstance(v, bmesh.types.BMVert)]
                bmesh.ops.translate(bm, vec=mathutils.Vector((0, 0, -0.2)), verts=extruded_verts)
                bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
                
                bm.to_mesh(mesh)
                bm.free()
                
                obj.is_IfcSlab = True
                obj.ifc_Thickness = 0.2
                context.collection.objects.link(obj)
                self.select_object(context, obj)

    def select_object(self, context, obj):
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            scene = context.scene
            if not hasattr(scene, "ifc_DrawSettings"):
                return {'CANCELLED'}
            
            settings = scene.ifc_DrawSettings
            
            # Toggle drawing mode off if it was already on
            if settings.is_drawing:
                settings.is_drawing = False
                return {'FINISHED'}
                
            settings.is_drawing = True
            self.drawn_points = []
            self.mouse_pos_3d = None
            
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_VIEW')
            
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found")
            return {'CANCELLED'}

    def finish(self, context):
        if hasattr(self, '_handle'):
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        if hasattr(context.scene, "ifc_DrawSettings"):
            context.scene.ifc_DrawSettings.is_drawing = False
        context.area.tag_redraw()

    def update_mouse_pos(self, context, event):
        region = context.region
        rv3d = context.region_data
        coord = event.mouse_region_x, event.mouse_region_y

        settings = context.scene.ifc_DrawSettings
        if settings.draw_shape == 'PICK':
            # Always update preview for pick mode
            self.drawn_points = self.get_pick_preview(context, event)
            self.mouse_pos_3d = None
            return

        from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d
        
        view_vector = region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = region_2d_to_origin_3d(region, rv3d, coord)
        
        plane_normal = mathutils.Vector((0, 0, 1))
        plane_point = mathutils.Vector((0, 0, 0))
        
        intersect = mathutils.geometry.intersect_line_plane(ray_origin, ray_origin + view_vector, plane_point, plane_normal)
        if intersect:
            self.mouse_pos_3d = intersect
            
            # Orthogonal snap by default, hold SHIFT to disable
            if hasattr(self, 'drawn_points') and len(self.drawn_points) > 0 and not event.shift:
                last_point = self.drawn_points[-1]
                delta = self.mouse_pos_3d - last_point
                if abs(delta.x) > abs(delta.y):
                    self.mouse_pos_3d.y = last_point.y
                else:
                    self.mouse_pos_3d.x = last_point.x

class DBIM_OT_start_tool(bpy.types.Operator):
    bl_idname = "dbim.start_tool"
    bl_label = "Start DBIM Tool"
    bl_description = "Helper operator to easily launch or toggle drawing modes"
    bl_options = {'REGISTER', 'UNDO'}
    
    target: bpy.props.StringProperty(name="Target Type", default="")
    shape: bpy.props.StringProperty(name="Draw Shape", default="")
    
    def execute(self, context):
        scene = context.scene
        if hasattr(scene, "ifc_DrawSettings"):
            settings = scene.ifc_DrawSettings
            
            # If the same shape is clicked while actively drawing, toggle it off
            if settings.is_drawing and self.shape and settings.draw_shape == self.shape:
                settings.is_drawing = False
                return {'FINISHED'}
                
            if self.target:
                settings.target_type = self.target
                if self.target in ['IfcWall', 'IfcGridAxis']:
                    settings.draw_system = 'IMMEDIATE'
                else:
                    settings.draw_system = 'BOUNDARY'
                    
                if self.target == 'IfcWall':
                    from ..props.props_wall import get_active_wall_type
                    get_active_wall_type(context.scene)
                    
                # Reset invalid shapes for the newly selected target
                if self.target == 'IfcGridAxis' and settings.draw_shape not in ['LINE', 'PICK']:
                    settings.draw_shape = 'LINE'
                elif self.target == 'IfcSlab' and settings.draw_shape not in ['LINE', 'RECTANGLE', 'CIRCLE']:
                    settings.draw_shape = 'LINE'
                    
            if self.shape:
                settings.draw_shape = self.shape
                
                if not settings.is_drawing:
                    # Find VIEW_3D to override context
                    view3d_area = next((a for a in context.screen.areas if a.type == 'VIEW_3D'), None)
                    if view3d_area:
                        view3d_region = next((r for r in view3d_area.regions if r.type == 'WINDOW'), None)
                        if view3d_region:
                            with context.temp_override(area=view3d_area, region=view3d_region):
                                bpy.ops.dbim.draw_mode('INVOKE_DEFAULT')
                        else:
                            self.report({'WARNING'}, "View3D Window Region not found")
                    else:
                        self.report({'WARNING'}, "View3D Area not found")
            else:
                # If no shape is provided, just make sure we are NOT drawing
                if settings.is_drawing:
                    settings.is_drawing = False
        return {'FINISHED'}
