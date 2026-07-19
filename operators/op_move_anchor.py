import bpy

class DBIM_OT_move_anchor(bpy.types.Operator):
    """Move Anchor (Click-Move-Click) with native snapping"""
    bl_idname = "dbim.move_anchor"
    bl_label = "Move Anchor"
    bl_options = {'REGISTER', 'UNDO'}

    anchor_index: bpy.props.IntProperty(name="Anchor Index", default=0) # 0 for start, 1 for end
    
    _timer = None
    _state = 0 # 0: waiting for initial release, 1: transforming, 2: finishing

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
        
        # Ensure only the empty is selected
        bpy.ops.object.select_all(action='DESELECT')
        self.empty.select_set(True)
        context.view_layer.objects.active = self.empty

        # Add modal handler FIRST so we get events before transform.translate
        context.window_manager.modal_handler_add(self)
        self._timer = context.window_manager.event_timer_add(0.01, window=context.window)
        self._state = 0

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        # Prevent errors if empty is accidentally deleted
        if getattr(self, 'empty', None) is None or self.empty.name not in bpy.data.objects:
            self.cleanup(context)
            return {'FINISHED'}

        # Synchronize location from Empty to Target Object
        if getattr(self, 'target_obj', None):
            if self.anchor_index == 0:
                self.target_obj.ifc_StartPoint = self.empty.location
            else:
                self.target_obj.ifc_EndPoint = self.empty.location
            # Force update to show changes in real-time
            self.target_obj.update_tag()

        # State 0: Wait for user to release mouse after clicking the gizmo
        if self._state == 0:
            if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
                self._state = 1
                # Invoke the built-in transform operator
                bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=(True, True, False), orient_type='GLOBAL')
            return {'PASS_THROUGH'}

        # State 1: Transforming (transform.translate is running natively)
        elif self._state == 1:
            if event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'ESC', 'RET'} and event.value == 'PRESS':
                # User confirmed or cancelled the translation.
                # transform.translate will consume this PRESS and finish.
                self._state = 2
            return {'PASS_THROUGH'}

        # State 2: Finishing
        elif self._state == 2:
            if event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'ESC', 'RET'} and event.value == 'RELEASE':
                self.cleanup(context)
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def cleanup(self, context):
        if getattr(self, '_timer', None):
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        
        if getattr(self, 'empty', None) and self.empty.name in bpy.data.objects:
            bpy.data.objects.remove(self.empty)
            self.empty = None
            
        if getattr(self, 'target_obj', None) and self.target_obj.name in bpy.data.objects:
            self.target_obj.select_set(True)
            context.view_layer.objects.active = self.target_obj
