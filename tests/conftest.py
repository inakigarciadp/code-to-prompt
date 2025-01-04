import sys
from pathlib import Path

# Get the absolute path of the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Add the project root directory to Python path
sys.path.insert(0, str(PROJECT_ROOT))
