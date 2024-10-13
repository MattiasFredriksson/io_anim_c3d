import bpy
import os
import unittest

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from test.zipload import Zipload


class ImportC3DTestMultipleFiles(unittest.TestCase):

    def setUpClass():
        Zipload.download_and_extract()
        objs = []
        actions = []

        # Parse files
        for filepath in Zipload.get_c3d_filenames('sample00'):
            # Parse
            bpy.ops.import_anim.c3d(filepath=filepath, print_file=False)
            # Fetch loaded objects
            obj = bpy.context.selected_objects[0]
            objs.append(obj)
            actions.append(obj.animation_data.action)

        ImportC3DTestMultipleFiles.objs = objs
        ImportC3DTestMultipleFiles.actions = actions

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
