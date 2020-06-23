
def islist(N):
    """
    Check if 'N' object is any type of array
    """
    return hasattr(N, '__len__') and (not isinstance(N, str))
