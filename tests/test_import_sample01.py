import bpy
import os
import unittest

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


class ImportC3DTestSample01(unittest.TestCase):

    ZIP_FOLDER = 'sample01'
    ZIP_FILES = \
        [
         'Eb015pi.c3d',
         'Eb015pr.c3d',
         'Eb015vi.c3d',
         'Eb015vr.c3d',
         'Eb015si.c3d',
         'Eb015sr.c3d'
        ]

    def setUpClass():
        from tests.zipload import Zipload
        from bpy_extras import anim_utils
        
        Zipload.download_and_extract()

        objs = []
        actions = []
        channelbags = []

        for file in ImportC3DTestSample01.ZIP_FILES:

            # Parse
            fp = Zipload.get_c3d_path('sample01', file)
            bpy.ops.import_anim.c3d(filepath=fp,
                                    print_file=False,
                                    include_empty_labels=False,
                                    perf_mon=False)
            # Fetch loaded objects
            obj = bpy.context.selected_objects[0]
            action = obj.animation_data.action
            action_slot = obj.animation_data.action_slot
            channelbag = anim_utils.action_get_channelbag_for_slot(action, action_slot)
            objs.append(obj)
            actions.append(action)
            channelbags.append(channelbag)

        ImportC3DTestSample01.objs = objs
        ImportC3DTestSample01.channelbags = channelbags

    def test_A_channel_count(self):
        ''' Verify number of channels are equal
        '''
        acb0 = self.channelbags[0]
        for channelbag in self.channelbags[1:]:
            self.assertEqual(len(acb0.fcurves), len(channelbag.fcurves))

    def test_B_tracker_names(self):
        ''' Verify labels for each channel group are equal and ordered
        '''
        acb0 = self.channelbags[0]
        for channelbag in self.channelbags[1:]:
            for i in range(len(acb0.fcurves)):
                self.assertEqual(acb0.fcurves[i].group.name, channelbag.fcurves[i].group.name)

    def test_C_tracker_labels(self):
        ''' Verify data labels match assigned channel group names
        '''
        LABELS = ['RFT1', 'RFT2', 'RFT3', 'LFT1', 'LFT2', 'LFT3', 'RSK1', 'RSK2', 'RSK3', 'RSK4', 'LSK1', 'LSK2',
                  'LSK3', 'LSK4', 'RTH1', 'RTH2', 'RTH3', 'RTH4', 'LTH1', 'LTH2', 'LTH3', 'LTH4', 'PV1', 'PV2', 'PV3',
                  'pv4']  # , 'TR2', 'TR3', 'RA', 'LA', 'RK', 'LK', 'RH', 'LH', 'RPP', 'LPP', 'RS', 'LS']

        for channelbag in self.channelbags:
            names = [fc_grp.name for fc_grp in channelbag.groups]
            for label in LABELS:
                self.assertIn(label, names)

    def test_D_keyframe_count(self):
        ''' Verify number of keyframes are identical
        '''
        acb0 = self.channelbags[0]
        for channelbag in self.channelbags[1:]:
            for i in range(len(acb0.fcurves)):
                self.assertEqual(len(acb0.fcurves[i].keyframe_points), len(channelbag.fcurves[i].keyframe_points))

    def test_E_keyframes_equal(self):
        ''' Verify keyframes are identical
        '''
        acb0 = self.channelbags[0]
        for channelbag in self.channelbags[1:]:
            for i in range(len(acb0.fcurves)):
                for ii in range(len(acb0.fcurves[i].keyframe_points)):
                    # co = (t, axis_co)
                    self.assertAlmostEqual(acb0.fcurves[i].keyframe_points[ii].co,
                                           channelbag.fcurves[i].keyframe_points[ii].co)


if __name__ == '__main__':
    import sys
    sys.argv = [__file__] + (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    unittest.main()
