import os
import sys
import subprocess
from dotenv import load_dotenv

print('Starting WhisperWriter...')
load_dotenv()
subprocess.run([sys.executable, '__run.py'])
