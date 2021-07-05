import bpy
import os
import unittest


class ImportC3DTestSample01(unittest.TestCase):

    def setUpClass():
        # Find import directory relative to __file__
        if '.blend' in __file__:
            # Fetch path from the text object in bpy.data.texts
            filename = os.path.basename(__file__)
            filepath =  bpy.data.texts[filename].filepath
        else:
            filepath = __file__
        IMPORT_DIR = os.path.join(os.path.dirname(filepath), '.\\testfiles\\sample01')

        FILES = ['Eb015pi.c3d', 'Eb015pr.c3d', 'Eb015si.c3d', 'Eb015sr.c3d', 'Eb015vi.c3d', 'Eb015vr.c3d']
        os.chdir(IMPORT_DIR)

        objs = []
        actions = []

        # Parse files
        for file in FILES:
            # Parse
            bpy.ops.import_anim.c3d(filepath=os.path.join(IMPORT_DIR, file),
                                    print_file=False,
                                    include_empty_labels=False)
            # Fetch loaded objects
            obj = bpy.context.selected_objects[0]
            objs.append(obj)
            actions.append(obj.animation_data.action)

        ImportC3DTestSample01.objs = objs
        ImportC3DTestSample01.actions = actions

    def test_A_channel_count(self):
        ''' Verify number of channels are equal
        '''
        a0 = self.actions[0]
        for action in self.actions[1:]:
            self.assertEqual(len(a0.fcurves), len(action.fcurves))

    def test_B_tracker_names(self):
        ''' Verify labels for each channel group are equal and ordered
        '''
        a0 = self.actions[0]
        for action in self.actions[1:]:
            for i in range(len(a0.fcurves)):
                self.assertEqual(a0.fcurves[i].group.name, action.fcurves[i].group.name)

    def test_C_tracker_labels(self):
        ''' Verify data labels match assigned channel group names
        '''
        LABELS = ['RFT1', 'RFT2', 'RFT3', 'LFT1', 'LFT2', 'LFT3', 'RSK1', 'RSK2', 'RSK3', 'RSK4', 'LSK1', 'LSK2',
                  'LSK3', 'LSK4', 'RTH1', 'RTH2', 'RTH3', 'RTH4', 'LTH1', 'LTH2', 'LTH3', 'LTH4', 'PV1', 'PV2', 'PV3',
                  'pv4']  # , 'TR2', 'TR3', 'RA', 'LA', 'RK', 'LK', 'RH', 'LH', 'RPP', 'LPP', 'RS', 'LS']

        for action in self.actions:
            names = [fc_grp.name for fc_grp in action.groups]
            for label in LABELS:
                self.assertIn(label, names)

    def test_D_keyframe_count(self):
        ''' Verify number of keyframes are identical
        '''
        a0 = self.actions[0]
        for action in self.actions[1:]:
            for i in range(len(a0.fcurves)):
                self.assertEqual(len(a0.fcurves[i].keyframe_points), len(action.fcurves[i].keyframe_points))

    def test_E_keyframes_equal(self):
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
