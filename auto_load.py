import os
import bpy
import sys
import typing
import inspect
import pkgutil
import importlib
from pathlib import Path

__all__ = (
    "init",
    "register",
    "unregister",
)

modules = None
ordered_classes = None

def init(package_name):
    global modules
    global ordered_classes

    modules = get_all_submodules(Path(__file__).parent, package_name)
    ordered_classes = get_ordered_classes_to_register(modules)

def register():
    for cls in ordered_classes:
        bpy.utils.register_class(cls)

    for module in modules:
        if module.__name__ == __name__:
            continue
        if hasattr(module, "register"):
            module.register()

def unregister():
    for cls in reversed(ordered_classes):
        bpy.utils.unregister_class(cls)

    for module in reversed(modules):
        if module.__name__ == __name__:
            continue
        if hasattr(module, "unregister"):
            module.unregister()

# Import modules
#################################################

def get_all_submodules(directory, package_name):
    return list(iter_submodules(directory, package_name))

def iter_submodules(path, package_name):
    for name in sorted(iter_submodule_names(path)):
        yield importlib.import_module("." + name, package_name)

def iter_submodule_names(path, root=""):
    for _, module_name, is_pkg in pkgutil.iter_modules([str(path)]):
        if is_pkg:
            sub_path = path / module_name
            sub_root = root + module_name + "."
            yield from iter_submodule_names(sub_path, sub_root)
        else:
            yield root + module_name

# Find classes to register
#################################################

def get_ordered_classes_to_register(modules):
    return toposort(get_register_deps_dict(modules))

def get_register_deps_dict(modules):
    my_classes = set(iter_classes_to_register(modules))
    my_classes_by_idname = {cls.bl_idname: cls for cls in my_classes if hasattr(cls, "bl_idname")}

    deps_dict = {}
    for cls in my_classes:
        deps_dict[cls] = set(iter_own_register_deps(cls, my_classes))
        for parent in cls.__bases__:
            if parent in my_classes:
                deps_dict[cls].add(parent)
        for subcls in cls.__subclasses__():
            if subcls in my_classes:
                if subcls not in deps_dict:
                    deps_dict[subcls] = set()
                deps_dict[subcls].add(cls)

    return deps_dict

def iter_own_register_deps(cls, my_classes):
    yield from (dep for dep in iter_classes_in_annotations(cls) if dep in my_classes)
    if getattr(cls, "bl_parent_id", None):
        for other_cls in my_classes:
            if getattr(other_cls, "bl_idname", None) == cls.bl_parent_id:
                yield other_cls

def iter_classes_in_annotations(cls):
    for ann in typing.get_type_hints(cls, {}, {}).values():
        if inspect.isclass(ann):
            yield ann

def iter_classes_to_register(modules):
    base_types = (
        bpy.types.Panel, bpy.types.Operator, bpy.types.PropertyGroup,
        bpy.types.AddonPreferences, bpy.types.Header, bpy.types.Menu,
        bpy.types.Node, bpy.types.NodeSocket, bpy.types.NodeTree,
        bpy.types.UIList, bpy.types.RenderEngine,
        bpy.types.Gizmo, bpy.types.GizmoGroup, bpy.types.Macro,
    )
    for cls in get_classes_in_modules(modules):
        if any(issubclass(cls, base) for base in base_types):
            if not getattr(cls, "is_registered", False):
                yield cls

def get_classes_in_modules(modules):
    classes = set()
    for module in modules:
        for cls in iter_classes_in_module(module):
            classes.add(cls)
    return classes

def iter_classes_in_module(module):
    for value in module.__dict__.values():
        if inspect.isclass(value):
            if getattr(value, "__module__", None) == module.__name__:
                yield value

# Topological sort
#################################################

def toposort(deps_dict):
    sorted_list = []
    sorted_values = set()
    while len(deps_dict) > 0:
        unsorted = []
        for value, deps in deps_dict.items():
            if len(deps) == 0:
                sorted_list.append(value)
                sorted_values.add(value)
            else:
                unsorted.append(value)
        deps_dict = {value: deps_dict[value] - sorted_values for value in unsorted}
    return sorted_list
