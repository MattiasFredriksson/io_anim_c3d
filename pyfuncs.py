import time

def new_sampler(init=False):
    if init:    return ([time.process_time()], [])
    else:       return ([], [])

def begin_sample(sampler):
    sampler[0].append(time.process_time())

def end_sample(sampler):
    sampler[1].append(time.process_time())

def mean_sample(sampler, first_sample=None, end_sample=None):
    import numpy
    diff = numpy.subtract(sampler[1], sampler[0])[first_sample:end_sample]
    return numpy.sum(diff) / len(diff)

def analyze_sample(sampler, first_sample=None, end_sample=None):
    import numpy
    diff = numpy.subtract(sampler[1], sampler[0])[first_sample:end_sample]
    sum = numpy.sum(diff)
    mean = numpy.sum(diff) / len(diff)
    return sum, mean

def islist(N):
	"""
	Check if 'N' object is any type of array
	"""
	return hasattr(N, '__len__') and (not isinstance(N, str))
