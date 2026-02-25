import subprocess
import os
import signal
import time
from typing import Iterable
from pynput.keyboard import Controller as PynputController, Key, KeyCode

from whisper_writer.utils import ConfigManager

def run_command_or_exit_on_failure(command: Iterable[str]) -> None:
    """
    Run a shell command and exit if it fails.

    Args:
        command (list): The command to run as a list of strings.
    """
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        exit(1)

class InputSimulator:
    """
    A class to simulate keyboard input using various methods.
    """

    def __init__(self) -> None:
        """
        Initialize the InputSimulator with the specified configuration.
        """
        self.input_method = ConfigManager.get_config_value('post_processing', 'input_method')
        self.dotool_process = None
        self.held_keys: set[Key | KeyCode] = set()

        if self.input_method == 'pynput':
            self.keyboard = PynputController()
        elif self.input_method == 'dotool':
            self._initialize_dotool()

    def _initialize_dotool(self) -> None:
        """
        Initialize the dotool process for input simulation.
        """
        self.dotool_process = subprocess.Popen("dotool", stdin=subprocess.PIPE, text=True)
        assert self.dotool_process.stdin is not None

    def _terminate_dotool(self) -> None:
        """
        Terminate the dotool process if it's running.
        """
        if self.dotool_process:
            os.kill(self.dotool_process.pid, signal.SIGINT)
            self.dotool_process = None

    def typewrite(self, text: str) -> None:
        """
        Simulate typing the given text with the specified interval between keystrokes.

        Args:
            text (str): The text to type.
        """
        interval: float = ConfigManager.get_config_value('post_processing', 'writing_key_press_delay')
        if self.input_method == 'pynput':
            self._typewrite_pynput(text, interval)
        elif self.input_method == 'ydotool':
            self._typewrite_ydotool(text, interval)
        elif self.input_method == 'dotool':
            self._typewrite_dotool(text, interval)

    def _typewrite_pynput(self, text: str, interval: float) -> None:
        """
        Simulate typing using pynput.

        Args:
            text (str): The text to type.
            interval (float): The interval between keystrokes in seconds.
        """
        for char in text:
            self.keyboard.press(char)
            self.keyboard.release(char)
            time.sleep(interval)

    def _typewrite_ydotool(self, text: str, interval: float) -> None:
        """
        Simulate typing using ydotool.

        Args:
            text (str): The text to type.
            interval (float): The interval between keystrokes in seconds.
        """
        cmd = "ydotool"
        run_command_or_exit_on_failure([
            cmd,
            "type",
            "--key-delay",
            str(interval * 1000),
            "--",
            text,
        ])

    def _typewrite_dotool(self, text: str, interval: float) -> None:
        """
        Simulate typing using dotool.

        Args:
            text (str): The text to type.
            interval (float): The interval between keystrokes in seconds.
        """
        assert self.dotool_process and self.dotool_process.stdin
        self.dotool_process.stdin.write(f"typedelay {interval * 1000}\n")
        self.dotool_process.stdin.write(f"type {text}\n")
        self.dotool_process.stdin.flush()

    def cleanup(self) -> None:
        """
        Perform cleanup operations, such as terminating the dotool process.
        """
        if self.input_method == 'dotool':
            self._terminate_dotool()

    def simulate_keypress(self, keys: Key | KeyCode | Iterable[Key | KeyCode], n: int = 1) -> None:
        """
        Press a collection of keys together 'n' times.
        """

        if not isinstance(keys, Iterable):
            keys = frozenset((keys,))

        for i in range(n):
            for key in keys:
                self.keyboard.press(key)

            for key in keys:
                self.keyboard.release(key)

    def press_and_hold_key(self, key: Key | KeyCode) -> None:
        self.held_keys.add(key)
        self.keyboard.press(key)

    def release_keys(self) -> None:
        for key in self.held_keys:
            self.keyboard.release(key)
        self.held_keys = set()

    class CommonKeypresses:
        UNDO = (Key.ctrl, KeyCode.from_char("z"))
        REDO = (Key.ctrl, KeyCode.from_char("y"))
        CUT = (Key.ctrl, KeyCode.from_char("x"))
        COPY = (Key.ctrl, KeyCode.from_char("c"))
        PASTE = (Key.ctrl, KeyCode.from_char("v"))
        SELECT_ALL = (Key.ctrl, KeyCode.from_char("a"))
        SAVE = (Key.ctrl, KeyCode.from_char("s"))
        CLEAR_FORMATTING = (Key.ctrl, Key.space, KeyCode.from_char("m")) # Combine word and libreoffice shortcut (ctrl+space & ctrl+m)
