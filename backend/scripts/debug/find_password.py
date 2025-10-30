import hashlib

current_hash = 'ccd96d4ace38ce3c9619160e8a999d1baddad2e500f7c33c9259a9cfe5d59681'
test_passwords = ['admin123', 'Admin123!', 'Admin123', 'admin', 'NewPassword123!', 'NewAdmin123!', 'TestNewPass123!', 'password123', 'Password123!']

print('Searching for password that matches current hash:')
print(f'Target hash: {current_hash}')
print()

for pwd in test_passwords:
    calculated = hashlib.sha256(pwd.encode()).hexdigest()
    match = (calculated == current_hash)
    print(f'{pwd:20} -> {calculated[:20]}... Match: {match}')
    if match:
        print(f'  *** FOUND: Password is "{pwd}" ***')