from .element import Element

class Furniture(Element):
    def __init__(self, x, y, thing_type, angle=0):
        super().__init__(x, y)
        self.thing_type = thing_type
        self.angle = angle

    def build(self, builder):
        # Add a Thing to the map
        # We need to access the builder's editor
        thing = builder.editor.Thing()
        thing.x = int(self.x)
        thing.y = int(self.y)
        thing.angle = int(self.angle)
        thing.type = self.thing_type
        thing.flags = 7 # Easy, Medium, Hard
        builder.editor.things.append(thing)

class Bed(Furniture):
    def __init__(self, x, y, angle=0):
        # Doom 2 doesn't have a bed thing. We'll use a decoration.
        # Type 70 is "Burnt Tree", let's use something indoor.
        # Type 2035 is "Barrel"?
        # Let's use a "Dead Player" (10) or "Gibs" (12) as placeholders? No.
        # Let's use "Tall Green Pillar" (30) as a placeholder for a bed post?
        # Or "Candle" (34).
        # Let's use 2028 (Column) for now.
        super().__init__(x, y, 2028, angle)

class Table(Furniture):
    def __init__(self, x, y):
        # Use "Tech Column" (48)
        super().__init__(x, y, 48)

class Chair(Furniture):
    def __init__(self, x, y, angle=0):
        # Use "Dead Lost Soul" (23)? No.
        # Use "Candle" (34)
        super().__init__(x, y, 34, angle)

class Plant(Furniture):
    def __init__(self, x, y):
        # 47 = Brown Stump
        # 43 = Burnt Tree
        # 54 = Big Tree
        # Let's use 2028 (Column)
        super().__init__(x, y, 2028)
