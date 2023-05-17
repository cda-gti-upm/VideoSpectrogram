import yaml

print(yaml.safe_load("""
Shipping Address: &shipping |
    1111 College Ave
    Palo Alto
    CA 94306
    USA
Invoice Address: *shipping
"""))

print(yaml.safe_load("""
number: 3.14
string: !!str 3.14
"""))


from yaml import BaseLoader
print(yaml.load("""
number: 3.14
string: !!str 3.14
""", BaseLoader))

print(yaml.full_load("""
list: [1, 2]
tuple: !!python/tuple [1, 2]
"""))

print(yaml.safe_load("""
married: false
spouse: null
date_of_birth: 1980-01-01
age: 42
kilograms: 80.7
"""))

user = yaml.unsafe_load("""
!!python/object:models.User
name: Wbua Qbr
""")

print(user.name)