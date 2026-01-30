from whisper_writer.input_simulation import InputSimulator

class Event:
    def undo(self) -> str:
        return ""

    def redo(self) -> str:
        return ""


class Write(Event):
    string: str # The written string

    def undo(self):
        return "\b" * len(self.string)

    def redo(self):
        return self.string


class Backspace(Event):
    string: str # The deleted string

    def undo(self):
        return self.string
    
    def redo(self):
        return "\b" * len(self.string)


class Select(Event):
    string: str # The selected string



class History:
    def __init__(self, input_simulator: InputSimulator):
        self.history: list[Event] = []
        self.cur_state: int = -1
        self.inputSimulator = input_simulator

    def add(self, msg: str) -> None:
        # If we are not at the end of the current history, we need to remove the rest of the history stack before we add to it
        if self.cur_state >= 0 and self.cur_state != len(self.history):
            self.history = self.history[:self.cur_state + 1]

        self.history.append(msg)
        self.cur_state += 1

    def undo(self) -> None:
        if self.cur_state < 0:
            return

        self.history[self.cur_state].undo()
        self.cur_state -= 1

    def redo(self) -> None:
        if self.cur_state >= len(self.history):
            return

        self.history[self.cur_state].redo()
        self.cur_state += 1
