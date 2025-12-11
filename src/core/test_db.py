# In Python console or new test file:
from src.core.database import get_database

db = get_database()

# Check if these exist:
print("update_user_profile exists:", hasattr(db, 'update_user_profile'))
print("update_profile exists:", hasattr(db, 'update_profile'))
print("update_user_preferences exists:", hasattr(db, 'update_user_preferences'))
print("update_preferences exists:", hasattr(db, 'update_preferences'))