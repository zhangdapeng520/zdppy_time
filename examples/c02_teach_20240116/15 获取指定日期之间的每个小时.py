import ztime
from datetime import datetime

start = datetime(2022, 1, 1, 1, 1, 1)
end = datetime(2022, 1, 2, 1, 1, 1)

hours = ztime.ZTime.span_range("hour", start, end)
print(hours)

for hour in hours:
    print(hour)
