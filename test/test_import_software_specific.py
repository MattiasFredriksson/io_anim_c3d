import bpy
import os
import unittest


class ImportC3DTestVicon(unittest.TestCase):

    def setUpClass():
        # Find import directory relative to __file__
        if '.blend' in __file__:
            # Fetch path from the text object in bpy.data.texts
            filename = os.path.basename(__file__)
            filepath = bpy.data.texts[filename].filepath
        else:
            filepath = __file__
        IMPORT_DIR = os.path.join(os.path.dirname(filepath), '.\\testfiles\\sample00\\Vicon Motion Systems')
        FILE = 'TableTennis.c3d'

        # Parse file
        bpy.ops.import_anim.c3d(filepath=os.path.join(IMPORT_DIR, FILE), print_file=False)
        # Fetch loaded objects
        obj = bpy.context.selected_objects[0]
        ImportC3DTestVicon.obj = obj
        ImportC3DTestVicon.action = obj.animation_data.action

    def test_A_channel_count(self):
        ''' Verify number action has channels
        '''
        EXPECTED = 243*3
        ch_count = len(self.action.fcurves)
        self.assertEqual(ch_count, EXPECTED)

    def test_B_keyframe_count(self):
        ''' Verify each channel has keyframes
        '''
        for fc in ImportC3DTestVicon.action.fcurves:
            self.assertGreater(len(fc.keyframe_points), 0)

    def test_C_tracker_labels(self):
        ''' Verify label array matches
        '''
        LABELS = ['Table:Table1', 'Table:Table2', 'Table:Table3', 'Table:Table4', 'Table:Table5', 'Table:Table6',
                  'Table:Table7', 'Table:Table8', 'Table:Table9', 'Player01:RFHD', 'Player01:RBHD', 'Player01:LFHD',
                  'Player01:RFHD', 'Player01:C7', 'Player01:T10', 'Player01:CLAV', 'Player01:STRN', 'Player01:RBAK',
                  'Player01:LSHO', 'Player01:LUPA', 'Player01:LELB', 'Player01:LWRA', 'Player01:LFRM', 'Player01:LWRB',
                  'Player01:RSHO', 'Player01:RELB', 'Player01:RWRA', 'Player01:RFIN', 'Player01:RASI', 'Player01:RPSI',
                  'Player01:LKNE', 'Player01:LANK', 'Player01:LTOE', 'Player01:RKNE', 'Player01:RANK', 'Player01:RTOE',
                  'Player01:LFIN', 'Player01:RUPA', 'Player01:RFRM', 'Player01:RWRB', 'Player01:LASI', 'Player01:LPSI',
                  'Player01:LTHI', 'Player01:LTIB', 'Player01:LHEE', 'Player01:RTHI', 'Player01:RTIB', 'Player01:RHEE',

                  'Player02:RFHD', 'Player02:RBHD', 'Player02:LFHD', 'Player02:RFHD', 'Player02:C7', 'Player02:T10',
                  'Player02:CLAV', 'Player02:STRN', 'Player02:RBAK', 'Player02:LSHO', 'Player02:LUPA', 'Player02:LELB',
                  'Player02:LWRA', 'Player02:LFRM', 'Player02:LWRB', 'Player02:RSHO', 'Player02:RELB', 'Player02:RWRA',
                  'Player02:RFIN', 'Player02:RASI', 'Player02:RPSI', 'Player02:LKNE', 'Player02:LANK', 'Player02:LTOE',
                  'Player02:RKNE', 'Player02:RANK', 'Player02:RTOE', 'Player02:LFIN', 'Player02:RUPA', 'Player02:RFRM',
                  'Player02:RWRB', 'Player02:LASI', 'Player02:LPSI', 'Player02:LTHI', 'Player02:LTIB', 'Player02:LHEE',
                  'Player02:RTHI', 'Player02:RTIB', 'Player02:RHEE',

                  'Player01:PELA', 'Player01:PELP', 'Player01:LFEA', 'Player01:LFEP', 'Player01:LTIA', 'Player01:LTIP',
                  'Player01:LFOA', 'Player01:LFOP', 'Player01:LTOA', 'Player01:LTOP', 'Player01:RFEA', 'Player01:RFEP',
                  'Player01:RTIA', 'Player01:RTIP', 'Player01:RFOA', 'Player01:RFOP', 'Player01:RTOA', 'Player01:RTOP',
                  'Player01:HEDA', 'Player01:HEDP', 'Player01:LCLA', 'Player01:LCLP', 'Player01:RCLA', 'Player01:RCLP',
                  'Player01:TRXA', 'Player01:TRXP', 'Player01:LHUA', 'Player01:LHUP', 'Player01:LRAA', 'Player01:LRAP',
                  'Player01:LHNA', 'Player01:LHNP', 'Player01:RHUA', 'Player01:RHUP', 'Player01:RRAA', 'Player01:RRAP',
                  'Player01:RHNA', 'Player01:RHNP',

                  'Player01:PELO', 'Player01:PELL', 'Player01:LFEO', 'Player01:LFEL', 'Player01:LTIO', 'Player01:LTIL',
                  'Player01:LFOO', 'Player01:LFOL', 'Player01:LTOO', 'Player01:LTOL', 'Player01:RFEO', 'Player01:RFEL',
                  'Player01:RTIO', 'Player01:RTIL', 'Player01:RFOO', 'Player01:RFOL', 'Player01:RTOO', 'Player01:RTOL',
                  'Player01:HEDO', 'Player01:HEDL', 'Player01:LCLO', 'Player01:LCLL', 'Player01:RCLO', 'Player01:RCLL',
                  'Player01:TRXO', 'Player01:TRXL', 'Player01:LHUO', 'Player01:LHUL', 'Player01:LRAO', 'Player01:LRAL',
                  'Player01:LHNO', 'Player01:LHNL', 'Player01:RHUO', 'Player01:RHUL', 'Player01:RRAO', 'Player01:RRAL',
                  'Player01:RHNO', 'Player01:RHNL',

                  'Player02:PELA', 'Player02:PELP', 'Player02:LFEA', 'Player02:LFEP', 'Player02:LTIA', 'Player02:LTIP',
                  'Player02:LFOA', 'Player02:LFOP', 'Player02:LTOA', 'Player02:LTOP', 'Player02:RFEA', 'Player02:RFEP',
                  'Player02:RTIA', 'Player02:RTIP', 'Player02:RFOA', 'Player02:RFOP', 'Player02:RTOA', 'Player02:RTOP',
                  'Player02:HEDA', 'Player02:HEDP', 'Player02:LCLA', 'Player02:LCLP', 'Player02:RCLA', 'Player02:RCLP',
                  'Player02:TRXA', 'Player02:TRXP', 'Player02:LHUA', 'Player02:LHUP', 'Player02:LRAA', 'Player02:LRAP',
                  'Player02:LHNA', 'Player02:LHNP', 'Player02:RHUA', 'Player02:RHUP', 'Player02:RRAA', 'Player02:RRAP',
                  'Player02:RHNA', 'Player02:RHNP',

                  'Player02:PELO', 'Player02:PELL', 'Player02:LFEO', 'Player02:LFEL', 'Player02:LTIO', 'Player02:LTIL',
                  'Player02:LFOO', 'Player02:LFOL', 'Player02:LTOO', 'Player02:LTOL', 'Player02:RFEO', 'Player02:RFEL',
                  'Player02:RTIO', 'Player02:RTIL', 'Player02:RFOO', 'Player02:RFOL', 'Player02:RTOO', 'Player02:RTOL',
                  'Player02:HEDO', 'Player02:HEDL', 'Player02:LCLO', 'Player02:LCLL', 'Player02:RCLO', 'Player02:RCLL',
                  'Player02:TRXO', 'Player02:TRXL', 'Player02:LHUO', 'Player02:LHUL', 'Player02:LRAO', 'Player02:LRAL',
                  'Player02:LHNO', 'Player02:LHNL', 'Player02:RHUO', 'Player02:RHUL', 'Player02:RRAO', 'Player02:RRAL',
                  'Player02:RHNO', 'Player02:RHNL',

                  'Player01:CentreOfMass', 'Player01:CentreOfMassFloor', 'Player01:CentreOfMass',
                  'Player01:CentreOfMassFloor']

        names = [fc_grp.name for fc_grp in ImportC3DTestVicon.action.groups]
        for label in LABELS:
            self.assertIn(label, names)


if __name__ == '__main__':
    import sys
    sys.argv = [__file__] + (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    unittest.main()
