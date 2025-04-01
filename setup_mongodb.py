from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables if .env file exists
try:
    load_dotenv()
except:
    pass

def setup_mongodb():
    """
    Set up MongoDB for OOTD analyzer
    - Creates database and collection
    - Sets up indexes
    - Tests connection with a sample document
    """
    # Get connection details from environment or use defaults
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    db_name = os.getenv("DB_NAME", "ootd_database")
    collection_name = os.getenv("COLLECTION_NAME", "outfits")
    
    print(f"Connecting to MongoDB at {mongo_uri}...")
    
    try:
        # Connect to MongoDB
        client = MongoClient(mongo_uri)
        
        # Test connection
        client.admin.command('ismaster')
        print("✅ MongoDB connection successful")
        
        # Access database and collection
        db = client[db_name]
        collection = db[collection_name]
        
        # Create indexes for faster queries
        collection.create_index("image")
        collection.create_index("type")
        collection.create_index("color")
        collection.create_index("analysis_date")
        print("✅ Indexes created successfully")
        
        # Insert a test document
        test_doc = {
            "image": "test_image.jpg",
            "type": "t-shirt",
            "color": "black",
            "analysis_date": datetime.now(),
            "test": True
        }
        
        result = collection.insert_one(test_doc)
        print(f"✅ Test document inserted with ID: {result.inserted_id}")
        
        # Find the document to verify
        found = collection.find_one({"test": True})
        print(f"✅ Found test document: {found['type']} in {found['color']}")
        
        # Remove the test document
        collection.delete_one({"test": True})
        print("✅ Test document removed")
        
        # Show existing collections
        collections = db.list_collection_names()
        print(f"Current collections in {db_name}: {collections}")
        
        print("\n✅ MongoDB setup complete! Your database is ready to use.")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up MongoDB: {str(e)}")
        
        if "refused" in str(e).lower():
            print("\n💡 TROUBLESHOOTING:")
            print("1. Make sure MongoDB service is running")
            print("   - Windows: Check Services app")
            print("   - macOS: Run 'brew services list'")
            print("   - Linux: Run 'sudo systemctl status mongodb'")
            print("2. If not running, start MongoDB:")
            print("   - Windows: Start service in Services app")
            print("   - macOS: Run 'brew services start mongodb-community'")
            print("   - Linux: Run 'sudo systemctl start mongodb'")
        
        return False

# Create .env file if it doesn't exist
def create_env_file():
    if not os.path.exists('.env'):
        print("Creating .env file with default MongoDB settings...")
        with open('.env', 'w') as f:
            f.write("OPENROUTER_API_KEY=your_api_key_here\n")
            f.write("MONGO_URI=mongodb://localhost:27017/\n")
            f.write("DB_NAME=ootd_database\n")
            f.write("COLLECTION_NAME=outfits\n")
            f.write("IMAGE_FOLDER=ootd_images\n")
            f.write("SITE_NAME=OOTD Analyzer\n")
        print("✅ Created .env file. Please edit it to add your OpenRouter API key.")
    else:
        print("✅ .env file already exists.")

# Create image folder if it doesn't exist
def create_image_folder():
    folder = os.getenv("IMAGE_FOLDER", "ootd_images")
    if not os.path.exists(folder):
        print(f"Creating image folder: {folder}")
        os.makedirs(folder)
        print(f"✅ Created folder: {folder}")
        print(f"   Please add your OOTD images to this folder.")
    else:
        print(f"✅ Image folder already exists: {folder}")

if __name__ == "__main__":
    print("==== OOTD Analyzer Database Setup ====\n")
    
    # Create config files
    create_env_file()
    create_image_folder()
    
    # Setup MongoDB
    if setup_mongodb():
        print("\n✨ All done! Your system is ready for OOTD analysis.")
        print("Next steps:")
        print("1. Edit the .env file to add your OpenRouter API key")
        print("2. Add your outfit images to the 'ootd_images' folder")
        print("3. Run the main script: python ootd_analyzer.py")
    else:
        print("\n❌ Setup incomplete. Please fix the errors and try again.")