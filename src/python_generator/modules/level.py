class Level:
    def __init__(self):
        self.rooms = []
        self.connectors = []
        self.next_tag = 1
        
    def get_new_tag(self):
        tag = self.next_tag
        self.next_tag += 1
        return tag
        
    def add_room(self, room):
        self.rooms.append(room)
        return room
        
    def add_connector(self, connector):
        self.connectors.append(connector)
        return connector
        
    def build(self, builder):
        # First, register cuts
        for conn in self.connectors:
            conn.register_cuts()
            
        # Build rooms
        for room in self.rooms:
            room.build(builder)
            
        # Build connectors
        for conn in self.connectors:
            conn.build(builder)
