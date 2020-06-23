
if "bpy" in locals():
    import importlib
    if "c3d" in locals():
        importlib.reload(c3d)

import bpy # Redundant import, only marks the directory as imported
from . import c3d
