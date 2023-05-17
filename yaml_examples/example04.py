import yaml

print(yaml.dump(3.14, Dumper=yaml.Dumper))
print(yaml.dump(3.14, Dumper=yaml.CDumper))  # C implementation

data = {"name": "John"}
print(yaml.dump(data))
import io
stream = io.StringIO()
print(yaml.dump(data, stream))
print(stream.getvalue())

with open("file1.yaml", mode="wt", encoding="utf-8") as file:
    yaml.dump(data, file)
with open("file2.yaml", mode="wb") as file:
    yaml.dump(data, file, encoding="utf-8")
