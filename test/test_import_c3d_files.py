import bpy
import glob
import os
import unittest

#import_dir = "C:\\Projects\\Code\\Blender\\Addons\\io_anim_c3d\\ignore"
#files = glob.glob("*.c3d")



class ImportC3DTestSample00(unittest.TestCase):

    def setUpClass():
        IMPORT_DIR = "C:\\Projects\\Code\\Blender\\Addons\\io_anim_c3d\\test\\testfiles\\sample01"
        os.chdir(IMPORT_DIR)
        FILES = glob.glob("*.c3d")

        objs = []
        actions = []

        # Parse files
        for file in FILES:
            # Parse
            bpy.ops.import_anim.c3d(filepath=os.path.join(IMPORT_DIR, file), print_file=False)
            # Fetch loaded objects
            obj = bpy.context.selected_objects[0]
            objs.append(obj)
            actions.append(obj.animation_data.action)

        ImportC3DTestSample00.objs = objs
        ImportC3DTestSample00.actions = actions

    def test_A_channel_count(self):
        ''' Verify loaded animations has channels
        '''
        for action in self.actions:
            self.assertGreater(len(action.fcurves), 0)


    def test_B_keyframe_count(self):
        ''' Verify each channel has keyframes
        '''
        for action in self.actions:
            for i in range(len(action.fcurves)):
                self.assertGreater(len(action.fcurves[i].keyframe_points), 0)


if __name__ == '__main__':
    import sys
    sys.argv = [__file__] + (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    unittest.main()
