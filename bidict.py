# Simple mock bidict implementation for testing
class bidict:
    def __init__(self, data_dict):
        self._forward = dict(data_dict)
        self._reverse = {v: k for k, v in data_dict.items()}
    
    def __getitem__(self, key):
        return self._forward[key]
    
    def __setitem__(self, key, value):
        self._forward[key] = value
        self._reverse[value] = key
    
    def __contains__(self, key):
        return key in self._forward
    
    def get(self, key, default=None):
        return self._forward.get(key, default)
    
    def items(self):
        return self._forward.items()
    
    def keys(self):
        return self._forward.keys()
    
    def values(self):
        return self._forward.values()