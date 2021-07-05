import bpy
import glob
import os

# Find import directory relative to __file__
if '.blend' in __file__:
    # Fetch path from the text object in bpy.data.texts
    filename = os.path.basename(__file__)
    filepath =  bpy.data.texts[filename].filepath
else:
    filepath = __file__

import_dir = os.path.join(os.path.dirname(filepath), '.\\testfiles\\sample01')

print(import_dir)
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
    bpy.ops.import_anim.c3d(filepath=file, print_file=False)
    # Fetch loaded objects
    obj = bpy.context.selected_objects[0]
    action = obj.animation_data.action
