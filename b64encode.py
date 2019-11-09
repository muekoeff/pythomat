import base64
import sys

for arg in sys.argv[1:]:
    print(base64.b64encode(arg))
