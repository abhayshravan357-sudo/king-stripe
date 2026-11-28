from getpass import getpass
from app.core.auth import hash_password

password = getpass("New King Stripe admin password: ")
if len(password) < 14:
    raise SystemExit("Use at least 14 characters")
print(hash_password(password))
