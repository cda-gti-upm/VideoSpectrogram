import os
import time
from subprocess import Popen
devnull = open(os.devnull, 'wb')
# Python >= 3.3 has subprocess.DEVNULL
Popen(['python', 'test_dash_app_1.py'], stdout=devnull, stderr=devnull)
print(os.getgid())
time.sleep(30)
