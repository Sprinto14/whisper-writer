from pynput import keyboard

from whisper_writer.input_simulation import InputSimulator


class Cursor:
    def __init__(self, input_simulator: InputSimulator) -> None:
        self.__loc = 0
        self.__last_loc = 0
        self.__input_simulator = input_simulator

    def get_loc(self) -> int:
        return self.__loc
    
    def set_loc(self, loc: int) -> None:
        self.__loc = loc
    
    def move_right(self) -> None: # Handle cursor at end of doc
        self.__input_simulator.simulate_keypress(keyboard.Key.right)
        self.__loc += 1

    def move_left(self) -> None:
        self.__input_simulator.simulate_keypress(keyboard.Key.left)
        self.__loc -= 1
        if self.__loc < 0:
            self.__loc = 0

    def move_to(self, loc: int) -> None:
        try:
            diff = loc - self.__loc
            if diff == 0:
                return

            move_key = keyboard.Key.right if diff > 0 else keyboard.Key.left
            self.__input_simulator.simulate_keypress(move_key, abs(diff))

        finally:
            self.__last_loc = self.__loc
            self.__loc = loc

    def move_back(self) -> None:
        self.move_to(self.__last_loc)
