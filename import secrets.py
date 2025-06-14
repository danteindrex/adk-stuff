import secrets
import string

# For JWT_SECRET_KEY (at least 32 characters)
jwt_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(40))
print(f"JWT_SECRET_KEY={jwt_key}")

# For ENCRYPTION_KEY (exactly 32 characters)
encryption_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
print(f"ENCRYPTION_KEY={encryption_key}")