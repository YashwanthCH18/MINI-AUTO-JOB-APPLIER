from app.database import db_service
import asyncio

async def get_users():
    try:
        # Try to query public.profiles
        result = db_service.client.table("profiles").select("id").limit(1).execute()
        if result.data:
            uid = result.data[0]['id']
            print(uid)
            with open("valid_user.txt", "w") as f:
                f.write(uid)
        else:
            print("No users found")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(get_users())
