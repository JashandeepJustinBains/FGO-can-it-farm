
class bidict(dict):
    def __init__(self, mapping):
        super().__init__(mapping)
        self.inverse = {v: k for k, v in mapping.items()}
