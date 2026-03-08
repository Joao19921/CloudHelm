import secrets
for _ in range(5):
    s = secrets.token_urlsafe(24)
    print(len(s), s)