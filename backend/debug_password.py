import hashlib
from app.db.database import get_db
from app.models.admin_model import Admin

# Get admin from database
db = next(get_db())
admin = db.query(Admin).first()
print(f'Admin password hash from DB: {admin.password_hash}')

# Test password
password = 'Admin123!'
calculated_hash = hashlib.sha256(password.encode()).hexdigest()
print(f'Calculated hash for "{password}": {calculated_hash}')
print(f'Hashes match: {admin.password_hash == calculated_hash}')

# Also test what the login is trying to use
login_password = 'admin123'
login_hash = hashlib.sha256(login_password.encode()).hexdigest()
print(f'Calculated hash for "{login_password}": {login_hash}')
print(f'Login hashes match: {admin.password_hash == login_hash}')