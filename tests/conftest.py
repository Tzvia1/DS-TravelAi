import os
import sys

# tools.py / contracts.py live at the project root, one level above tests/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
