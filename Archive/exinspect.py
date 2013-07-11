import inspect
import os

print inspect.getfile(inspect.currentframe())
print os.path.abspath(inspect.getfile(inspect.currentframe()))
print os.path.dirname(inspect.getfile(inspect.currentframe()))
print os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
