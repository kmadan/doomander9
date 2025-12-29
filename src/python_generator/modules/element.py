class Element:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def build(self, builder) -> None:
        raise NotImplementedError
