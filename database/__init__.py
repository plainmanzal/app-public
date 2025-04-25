import os
import sys

# Add parent directory to Python path to make package imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from database.user_db import (
    create_user_tables,
    create_connection,
    log_daily_journal_entry,
    add_journal_dish,
    add_rating
)
from database.menu_db import (
    create_wfr_tables,
    get_meals,
    get_dishes_from_menu
)

def initialize_databases():
    """Creates all necessary databases and tables."""
    create_user_tables()
    create_wfr_tables()

__all__ = [
    'initialize_databases',
    'create_connection',
    'create_user_tables',
    'create_wfr_tables',
    'log_daily_journal_entry',
    'add_journal_dish',
    'add_rating',
    'get_meals',
    'get_dishes_from_menu'
]