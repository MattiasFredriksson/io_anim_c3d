import bpy
import os
import unittest

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


class ImportC3DTestMultipleFiles(unittest.TestCase):

    def setUpClass():
        from tests.zipload import Zipload
        from bpy_extras import anim_utils

        Zipload.download_and_extract()
        objs = []
        actions = []
        channelbags = []

        # Parse files
        for filepath in Zipload.get_c3d_filenames('sample00'):
            # Parse
            bpy.ops.import_anim.c3d(filepath=filepath, print_file=False, perf_mon=False)
            # Fetch loaded objects
            obj = bpy.context.selected_objects[0]
            action = obj.animation_data.action
            action_slot = obj.animation_data.action_slot
            channelbag = anim_utils.action_get_channelbag_for_slot(action, action_slot)
            objs.append(obj)
            actions.append(action)
            channelbags.append(channelbag)

        ImportC3DTestMultipleFiles.objs = objs
        ImportC3DTestMultipleFiles.channelbags = channelbags

    def test_A_channel_count(self):
        ''' Verify loaded animations has channels
        '''
        self.assertGreater(len(self.channelbags), 0)
        for channelbag in self.channelbags:
            self.assertGreater(len(channelbag.fcurves), 0)

    def test_B_keyframe_count(self):
        ''' Verify each channel has keyframes
        '''
        self.assertGreater(len(self.channelbags), 0)
        for channelbag in self.channelbags:
            for i in range(len(channelbag.fcurves)):
                self.assertGreater(len(channelbag.fcurves[i].keyframe_points), 0)


if __name__ == '__main__':
    import sys
    sys.argv = [__file__] + (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    unittest.main()
