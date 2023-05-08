# Initialization
print("Initialization")
print("----------------")
from obspy.core import UTCDateTime
print(UTCDateTime("2012-09-07T12:15:00"))
print(UTCDateTime(2012, 9, 7, 12, 15, 0))
print(UTCDateTime(1347020100.0))
# timezones
print(UTCDateTime("2012-09-07T12:15:00+02:00"))
# Current time
print(UTCDateTime())

# Attribute Access
print("\nAttribute Access")
print("--------------------")
time = UTCDateTime("2012-09-07T12:15:00")
print(time.year)
print(time.julday)
print(time.timestamp)
print(time.weekday)

# Handling time differences
print("\nHandling time differences")
print("-----------------------------")
time = UTCDateTime("2012-09-07T12:15:00")
print(time + 3600)
time2 = UTCDateTime(2012, 1, 1)
print(time - time2)