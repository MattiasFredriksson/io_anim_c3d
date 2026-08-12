''' Verify the parameter section is read completely when the declared
    parameter block count understates the section's true span.

    Some writers (observed with OptiTrack Motive) declare fewer blocks than
    the section occupies, and the single-byte count field saturates at 255
    for files with larger sections (several thousand point labels), so
    parameters stored beyond the declared count (such as POINT:UNITS) were
    silently dropped. The reader widens the bound to the span implied by
    the header's data block index.

    Pure parser test (no bpy required); runs under tests/run.sh like the
    other test files.
'''
import io
import struct
import unittest

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from c3d import Reader
from tests.zipload import Zipload


ZIP = 'sample01.zip'
INTEL_FILE = 'Eb015pi.c3d'


def parameter_signature(reader):
    ''' Map of GROUP:PARAM -> raw parameter bytes, for parse equality. '''
    signature = {}
    for gname, group in reader.items():
        for pname, param in group.items():
            signature['%s:%s' % (gname, pname)] = param.bytes_value
    return signature


def doctor_declared_block_count(data, declared_blocks):
    ''' Overwrite the parameter section's block count byte. '''
    buf = bytearray(data)
    param_block = buf[0]
    buf[(param_block - 1) * 512 + 2] = declared_blocks
    return bytes(buf)


class ParameterSectionBoundTest(unittest.TestCase):

    def setUpClass():
        Zipload.download()
        ParameterSectionBoundTest.data = Zipload.read_c3d(ZIP, INTEL_FILE).read()

    def test_A_underdeclared_block_count_reads_all_parameters(self):
        reference = parameter_signature(Reader(io.BytesIO(self.data)))
        # Sanity: the reference file's parameter section spans several blocks.
        param_block = self.data[0]
        declared = self.data[(param_block - 1) * 512 + 2]
        self.assertGreater(declared, 2, 'fixture parameter section unexpectedly small')

        doctored = doctor_declared_block_count(self.data, 2)
        truncated_read = parameter_signature(Reader(io.BytesIO(doctored)))
        self.assertEqual(truncated_read, reference,
                         'parameters lost with under-declared block count: missing %s' %
                         sorted(set(reference) - set(truncated_read)))

    def test_B_declared_block_count_of_one_reads_all_parameters(self):
        # The pathological floor: everything beyond the first 512 bytes of
        # the section depends on the data-block bound.
        reference = parameter_signature(Reader(io.BytesIO(self.data)))
        doctored = doctor_declared_block_count(self.data, 1)
        self.assertEqual(parameter_signature(Reader(io.BytesIO(doctored))), reference)

    def test_C_consistent_file_unchanged(self):
        # A file whose declared count matches the true span parses as before
        # and carries POINT:UNITS.
        param_block = self.data[0]
        declared = self.data[(param_block - 1) * 512 + 2]
        data_block = struct.unpack('<H', self.data[16:18])[0]
        self.assertEqual(declared, data_block - param_block)
        self.assertIn('POINT:UNITS', parameter_signature(Reader(io.BytesIO(self.data))))


if __name__ == '__main__':
    import sys
    sys.argv = [__file__] + (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    unittest.main()
