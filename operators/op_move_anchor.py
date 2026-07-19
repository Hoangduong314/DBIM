import bpy

class DBIM_OT_move_anchor(bpy.types.Operator):
    """Move Anchor (Click-Move-Click) with native snapping"""
    bl_idname = "dbim.move_anchor"
    bl_label = "Move Anchor"
    bl_options = {'REGISTER', 'UNDO'}

    anchor_index: bpy.props.IntProperty(name="Anchor Index", default=0) # 0 for start, 1 for end
    
    _timer = None

    def invoke(self, context, event):
        self.target_obj = context.active_object
        if not self.target_obj:
            return {'CANCELLED'}

        # Get the anchor's initial 3D position
        if self.anchor_index == 0:
            anchor_loc = tuple(self.target_obj.ifc_StartPoint)
        else:
            anchor_loc = tuple(self.target_obj.ifc_EndPoint)

        # Create the Dummy Empty
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=anchor_loc)
        self.empty = context.active_object
        self.empty.name = "DBIM_Temp_Anchor"
        
        # Hide it? It's fine to leave it visible to give visual feedback
        # Ensure only the empty is selected
        bpy.ops.object.select_all(action='DESELECT')
        self.empty.select_set(True)
        context.view_layer.objects.active = self.empty

        # Add modal timer
        self._timer = context.window_manager.event_timer_add(0.01, window=context.window)
        context.window_manager.modal_handler_add(self)

        # Invoke the built-in transform operator
        # (True, True, False) limits translation to X and Y axes, locking Z
        bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=(True, True, False), constraint_orientation='GLOBAL')

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        # Prevent errors if empty is accidentally deleted
        if not self.empty or self.empty.name not in bpy.data.objects:
            self.cleanup(context)
            return {'FINISHED'}

        # Synchronize location from Empty to Target Object
        if self.target_obj:
            if self.anchor_index == 0:
                self.target_obj.ifc_StartPoint = self.empty.location
            else:
                self.target_obj.ifc_EndPoint = self.empty.location

        # When transform.translate finishes, it does NOT send a special event to our operator.
        # But we can detect if the user clicks LEFTMOUSE, RIGHTMOUSE, ESC, or RET.
        # transform.translate runs modally and handles these events, but our timer STILL runs.
        # Wait, if transform.translate handles LEFTMOUSE, we might receive it as PASS_THROUGH.
        # Actually, if transform.translate is finished, it returns {'FINISHED'}, and the active operator drops.
        # In Blender, if the active object is NO LONGER being transformed, the transform modal is dead.
        # How to check if transform is dead?
        # A robust way: if event type is one of the termination keys and value is RELEASE or PRESS.
        
        if event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'ESC', 'RET'} and event.value == 'RELEASE':
            # Cleanup
            self.cleanup(context)
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def cleanup(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        
        if getattr(self, 'empty', None) and self.empty.name in bpy.data.objects:
            bpy.data.objects.remove(self.empty)
            self.empty = None
            
        if getattr(self, 'target_obj', None) and self.target_obj.name in bpy.data.objects:
            self.target_obj.select_set(True)
            context.view_layer.objects.active = self.target_obj
