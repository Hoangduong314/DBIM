bl_info = {
    "name": "DBIM",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > DBIM",
    "description": "BIM tools for Blender",
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}

import bpy
from . import auto_load
from .core import gpu_grid_draw

auto_load.init(__name__)

def register():
    auto_load.register()
    gpu_grid_draw.register()

def unregister():
    gpu_grid_draw.unregister()
    auto_load.unregister()
