import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_mongo():
    """Test MongoDB connection"""
    mongo_uri = os.getenv("MONGO_URI")
    print(f"MongoDB URI: {mongo_uri[:30]}...")
    
    try:
        from pymongo import MongoClient
        from pymongo.errors import ServerSelectionTimeoutError
        
        print("🔍 Testing MongoDB connection...")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Test database access
        db_name = mongo_uri.split('/')[-1].split('?')[0]
        db = client[db_name]
        print(f"✅ Database '{db_name}' accessible")
        
        # List collections
        collections = db.list_collection_names()
        print(f"✅ Collections: {collections}")
        
    except ServerSelectionTimeoutError as e:
        print(f"❌ MongoDB connection timeout: {e}")
        print("This could be due to:")
        print("  1. Network connectivity issues")
        print("  2. MongoDB Atlas firewall settings")
        print("  3. Incorrect URI or credentials")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_mongo())