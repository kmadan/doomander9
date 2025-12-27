class Element:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def build(self, builder):
        raise NotImplementedError
