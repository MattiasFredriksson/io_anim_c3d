import bpy
import glob
import os
import unittest

#import_dir = "C:\\Projects\\Code\\Blender\\Addons\\io_anim_c3d\\ignore"
#files = glob.glob("*.c3d")



class ImportC3DTestVicon(unittest.TestCase):

    def setUpClass():
        IMPORT_DIR = "C:\\Projects\\Code\\Blender\\Addons\\io_anim_c3d\\test\\testfiles\\sample00\\Vicon Motion Systems"
        FILE = 'TableTennis.c3d'


        # Parse file
        bpy.ops.import_anim.c3d(filepath=os.path.join(IMPORT_DIR, FILE), print_file=False)
        # Fetch loaded objects
        ImportC3DTestVicon.obj = bpy.context.selected_objects[0]
        ImportC3DTestVicon.action = obj.animation_data.action


    def test_A_channel_count(self):
        ''' Verify number of channels loaded
        '''
        EXPECTED = 
        ch_count = len(self.action.fcurves)
        self.assertGreater(, 0)


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
