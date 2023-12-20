import os
import time
import subprocess
devnull = open(os.devnull, 'wb')
# Python >= 3.3 has subprocess.DEVNULL
proc = subprocess.Popen(['python', 'test_dash_app_1.py'], stdout=devnull, stderr=devnull)
time.sleep(60)
proc.kill()

