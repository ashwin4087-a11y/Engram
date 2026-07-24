import sys
print("Python executable:", sys.executable)
print("sys.path:")
for p in sys.path:
    print(" ", p)
try:
    import structlog
    print("\nstructlog FOUND at:", structlog.__file__)
except ImportError as e:
    print("\nstructlog NOT FOUND:", e)
