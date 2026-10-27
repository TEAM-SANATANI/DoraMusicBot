from pyrogram import Client

print("=== Dora Music Bot Assistant String Session Generator ===")
api_id = int(input("Enter API_ID: "))
api_hash = input("Enter API_HASH: ")

with Client("DoraSessionGen", api_id=api_id, api_hash=api_hash) as app:
    print("\n" + "="*50)
    print("Aapka STRING_SESSION yeh raha (Aap isse safely save kar lein):")
    print("="*50 + "\n")
    print(app.export_session_string())
    print("\n" + "="*50)
