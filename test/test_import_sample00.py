import bpy
import glob
import os
import unittest

#import_dir = "C:\\Projects\\Code\\Blender\\Addons\\io_anim_c3d\\ignore"
#files = glob.glob("*.c3d")



class ImportC3DTestSample00(unittest.TestCase):

    def setUpClass():
        IMPORT_DIR = "C:\\Projects\\Code\\Blender\\Addons\\io_anim_c3d\\test\\testfiles\\sample01"
        FILES = ['Eb015pi.c3d', 'Eb015pr.c3d', 'Eb015si.c3d', 'Eb015sr.c3d', 'Eb015vi.c3d', 'Eb015vr.c3d']
        os.chdir(IMPORT_DIR)

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
        ''' Verify number of channels are equal
        '''
        a0 = self.actions[0]
        for action in self.actions[1:]:
            self.assertEqual(len(a0.fcurves), len(action.fcurves))

    def test_B_channel_names(self):
        ''' Verify channel names are equal and ordered
        '''
        a0 = self.actions[0]
        for action in self.actions[1:]:
            for i in range(len(a0.fcurves)):
                self.assertEqual(a0.fcurves[i].group.name, action.fcurves[i].group.name)


    def test_C_keyframe_count(self):
        ''' Verify number of keyframes are identical
        '''
        a0 = self.actions[0]
        for action in self.actions[1:]:
            for i in range(len(a0.fcurves)):
                self.assertEqual(len(a0.fcurves[i].keyframe_points), len(action.fcurves[i].keyframe_points))


    def test_D_keyframes_equal(self):
        ''' Verify keyframes are identical
        '''
        a0 = self.actions[0]
        for action in self.actions[1:]:
            for i in range(len(a0.fcurves)):
                for ii in range(len(a0.fcurves[i].keyframe_points)):
                    # co = (t, axis_co)
                    self.assertAlmostEqual(a0.fcurves[i].keyframe_points[ii].co,
                                           action.fcurves[i].keyframe_points[ii].co)


if __name__ == '__main__':
    import sys
    sys.argv = [__file__] + (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    unittest.main()
