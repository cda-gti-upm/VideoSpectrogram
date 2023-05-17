import datetime
import json

person = {
    "firstName": "John",
    "dateOfBirth": datetime.date(1969, 12, 31),
    "married": False,
    "spouse": None,
    "children": ["Bobby", "Molly"],
}

print(json.dumps(person, indent=4, default=str))