import yaml

print(yaml.safe_load("name: Иван"))
print(yaml.safe_load(b"name: \xd0\x98\xd0\xb2\xd0\xb0\xd0\xbd"))
yaml.safe_load("name: Иван".encode("utf-8"))
yaml.safe_load("name: Иван".encode("utf-16"))
# Not supported: yaml.safe_load("name: Иван".encode("utf-32"))

with open("sample.yaml", mode="wb") as file:
    file.write(b"name: \xd0\x98\xd0\xb2\xd0\xb0\xd0\xbd")
# Text mode
with open("sample.yaml", mode="rt", encoding="utf-8") as file:
    print(yaml.safe_load(file))
# Binary mode
with open("sample.yaml", mode="rb") as file:
    print(yaml.safe_load(file))

import io
yaml.safe_load(io.StringIO("name: Иван"))
yaml.safe_load(io.BytesIO(b"name: \xd0\x98\xd0\xb2\xd0\xb0\xd0\xbd"))

# Load multiple documents
stream = """\
---
3.14
---
name: John Doe
age: 53
---
- apple
- banana
- orange
"""

for document in yaml.safe_load_all(stream):
    print(document)
