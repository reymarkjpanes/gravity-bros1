class StateManager:
    def __init__(self):
        self.state = 'MAIN_MENU'
        self.save_data = {}
        
    def set_state(self, new_state):
        self.state = new_state
        
    def get_state(self):
        return self.state
