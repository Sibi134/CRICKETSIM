import os
import sys

# Append the 'backend' directory to the Python path so it can import 'app.main'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
