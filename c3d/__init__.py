

if "bpy" in locals():
    import importlib
    if "c3d" in locals():
        importlib.reload(c3d)

# Importing bpy here marks the package as already imported when reloading
# (during the check for '"bpy" in locals' above)
import bpy
from . import c3d
