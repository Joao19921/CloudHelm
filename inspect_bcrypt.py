import inspect, passlib.handlers.bcrypt as b
print('path repr:', repr(b.__file__))

# attempt to locate detect_wrap_bug or related functions
for name in dir(b):
    if 'wrap' in name or 'bug' in name:
        print('attribute', name)

# read some relevant lines in file manually
import linecache
for i in range(350, 460):
    line = linecache.getline(b.__file__, i)
    if line:
        print(f"{i}: {line.rstrip()}")
