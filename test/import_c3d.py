import bpy
import glob
import os

import_dir = "C:\\Projects\\Code\\Blender\\Addons\\io_anim_c3d\\ignore"
import_dir = "C:\\Projects\\Code\\Blender\\Addons\\io_anim_c3d\\test\\testfiles\\sample01"
os.chdir(import_dir)
files = glob.glob("*.c3d")

b = 0
e = len(files)
files = files[b:e]

armature_obj = None


print('Matching files: ' + str(len(files)))
if len(files) == 0:
    raise Exception('No matching files found')

# Parse files
for file in files:
    # Parse
    bpy.ops.import_anim.c3d(filepath=file, load_mem_efficient=False)
    # Fetch loaded objects
    obj = bpy.context.selected_objects[0]
    action = obj.animation_data.action
