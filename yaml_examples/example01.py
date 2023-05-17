import yaml

email_message = """\
message:
  date: 2022-01-16 12:46:17Z
  from: john.doe@domain.com
  to:
    - bobby@domain.com
    - molly@domain.com
  cc:
    - jane.doe@domain.com
  subject: Friendly reminder
  content: |
    Dear XYZ,

    Lorem ipsum dolor sit amet...
  attachments:
    image1.gif: !!binary
        R0lGODdhCAAIAPAAAAIGAfr4+SwAA
        AAACAAIAAACDIyPeWCsClxDMsZ3CgA7
"""

# Load yaml content
print(yaml.safe_load(email_message))

# Save yaml (serialize) python variables
print(yaml.safe_dump(yaml.safe_load(email_message)))

# Equivalently
'''
from yaml import load, SafeLoader
load(email_message, SafeLoader)
'''

# To use C implementation
# First, you try importing one of the loader classes prefixed with the letter C to denote the use of the C library
# binding. If that fails, then you import a corresponding class implemented in Python
'''
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

SafeLoader
'''