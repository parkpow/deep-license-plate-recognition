import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from logger_setup import setup_logging
from status_checker import check_task_status

if __name__ == '__main__':
    setup_logging()
    check_task_status()
