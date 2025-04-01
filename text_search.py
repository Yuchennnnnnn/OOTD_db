import os
from pymongo import MongoClient
from dotenv import load_dotenv
from PIL import Image
import matplotlib.pyplot as plt

# Load environment variables from .env if available
load_dotenv()

def get_mongo_collection():
    # Get MongoDB connection details from environment variables or use defaults
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    db_name = os.getenv("DB_NAME", "ootd_database")
    collection_name = os.getenv("COLLECTION_NAME", "outfits")
    
    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]
    
    # Create a text index on 'type' and 'color' if it doesn't exist.
    collection.create_index([("type", "text"), ("color", "text")])
    
    return collection

def text_based_image_search(prompt):
    collection = get_mongo_collection()
    
    # Build a text search query using the user prompt.
    query = {"$text": {"$search": prompt}}
    # Project the text score along with fields you might want to display.
    projection = {
        "score": {"$meta": "textScore"},
        "image": 1,
        "type": 1,
        "color": 1
    }
    
    # Find the best match by sorting by the text score
    results = list(
        collection.find(query, projection)
        .sort([("score", {"$meta": "textScore"})])
        .limit(1)
    )
    
    if results:
        best_match = results[0]
        print("Best match found:")
        print(f"Image: {best_match.get('image')}")
        print(f"Type: {best_match.get('type')}")
        print(f"Color: {best_match.get('color')}")
        # Return the image filename so it can be displayed
        return best_match.get('image')
    else:
        print("No matching outfit found.")
        return None

def display_image(image_filename):
    # Get the image folder from environment variables or use default
    image_folder = os.getenv("IMAGE_FOLDER", "ootd_images")
    image_path = os.path.join(image_folder, image_filename)
    
    # Check if the file exists
    if not os.path.exists(image_path):
        print(f"Image file not found: {image_path}")
        return
    
    # Open and display the image using Pillow and matplotlib
    try:
        img = Image.open(image_path)
        plt.imshow(img)
        plt.axis('off')  # Hide axes
        plt.title(f"Displaying: {image_filename}")
        plt.show()
    except Exception as e:
        print(f"Error displaying image: {e}")

if __name__ == "__main__":
    # Get user input prompt
    user_prompt = input("Enter your search prompt (e.g., 'Show me an OOTD featuring green sneakers.'): ")
    match_filename = text_based_image_search(user_prompt)
    
    if match_filename:
        display_image(match_filename)

