# ##### BEGIN GPL LICENSE BLOCK #####
#
#  io_anim_c3d is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

# Script copyright (C) Campbell Barton, Bastien Montagne, Mattias Fredriksson


# ##### Performance monitor #####

DO_PERFMON = True

if DO_PERFMON:

    import time

    def new_sampler(init=False):
        if init:
            return ([time.process_time()], [])
        else:
            return ([], [])

    def begin_sample(sampler):
        sampler[0].append(time.process_time())

    def end_sample(sampler):
        sampler[1].append(time.process_time())

    def analyze_sample(sampler, first_sample=None, end_sample=None):
        import numpy
        diff = numpy.subtract(sampler[1], sampler[0])[first_sample:end_sample]
        sum = numpy.sum(diff)
        mean = numpy.sum(diff) / len(diff)
        return sum, mean

    class PerfMon():
        def __init__(self):
            self.level = -1
            self.ref_time = []

        def level_up(self, message="", init_sample=False):
            self.level += 1
            self.ref_time.append(time.process_time() if init_sample else None)
            if message:
                print("\t" * self.level, message, sep="")

        def level_down(self, message=""):
            if not self.ref_time:
                if message:
                    print(message)
                return
            ref_time = self.ref_time[self.level]
            print("\t" * self.level,
                  "\tDone (%f sec)\n" % ((time.process_time() - ref_time) if ref_time is not None else 0.0),
                  sep="")
            if message:
                print("\t" * self.level, message, sep="")
            del self.ref_time[self.level]
            self.level -= 1

        def step(self, message=""):
            ref_time = self.ref_time[self.level]
            curr_time = time.process_time()
            if ref_time is not None:
                print("\t" * self.level, "\tDone (%f sec)\n" % (curr_time - ref_time), sep="")
            self.ref_time[self.level] = curr_time
            print("\t" * self.level, message, sep="")

        def message(self, message):
            print("\t" * self.level, message, sep="")


else:

    def new_sampler(init=False):
        return None

    def begin_sample(sampler):
        pass

    def end_sample(sampler):
        pass

    def analyze_sample(sampler, first_sample=None, end_sample=None):
        return 0.0, 0.0

    class PerfMon():
        def __init__(self):
            pass

        def level_up(self, message=""):
            pass

        def level_down(self, message=""):
            pass

        def step(self, message=""):
            pass

        def message(self, message):
            pass
