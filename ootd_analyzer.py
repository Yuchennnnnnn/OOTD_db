from openai import OpenAI
import base64
import os
import csv
from pymongo import MongoClient
from datetime import datetime
import time
import logging
from dotenv import load_dotenv
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ootd_processing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
# Initialize clients
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=api_key,
)


# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "ootd_database")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "outfits")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

def encode_image(image_path):
    """Encode image to base64"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encoding image {image_path}: {str(e)}")
        return None

def analyze_ootd(image_path, max_retries=3):
    """Send image to API for analysis with retry mechanism"""
    base64_image = encode_image(image_path)
    if not base64_image:
        return None
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "http://localhost:8000",  # Local development placeholder
                    "X-Title": os.getenv("SITE_NAME", "OOTD Analyzer"),
                },
                model="bytedance-research/ui-tars-72b:free",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this outfit carefully. 
                                For each visible clothing item, provide:
                                1. Type: [exact clothing type]
                                2. Color: [specific color]
                                
                                Format each item on a new line as: 'Type: [type], Color: [color]'
                                Be very specific about both type (e.g., 'crew neck t-shirt' not just 'shirt') 
                                and color (e.g., 'navy blue' not just 'blue')."""
                            },
                            {
                                "type": "image_url",
                                "image_url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        ]
                    }
                ],
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed: {str(e)}")
            if attempt < max_retries - 1:
                # Exponential backoff
                time.sleep(2 ** attempt)
            else:
                logger.error(f"All retries failed for {image_path}")
                return None

def parse_response(response_text, image_filename):
    """Parse the API response into structured data using regex for more robust extraction"""
    if not response_text:
        return []
    
    items = []
    # Look for patterns like "Type: something, Color: something" with variations
    pattern = r"(?:Type|type)[:\s]+([^,]+),\s*(?:Color|color)[:\s]+(.+?)(?:\n|$)"
    matches = re.finditer(pattern, response_text)
    
    for match in matches:
        if len(match.groups()) >= 2:
            type_part = match.group(1).strip()
            color_part = match.group(2).strip()
            
            items.append({
                'image': image_filename,
                'type': type_part,
                'color': color_part,
                'raw_text': response_text,  # Store the original response for debugging
                'analysis_date': datetime.now()
            })
    
    # If regex didn't find anything, fallback to the original line-by-line parsing
    if not items:
        lines = [line.strip() for line in response_text.split('\n') if line.strip()]
        for line in lines:
            if ('type:' in line.lower() or 'type' in line.lower()) and ('color:' in line.lower() or 'color' in line.lower()):
                try:
                    parts = line.split(',')
                    type_part = parts[0].split('Type:' if 'Type:' in parts[0] else 'type:')[1].strip()
                    color_part = parts[1].split('Color:' if 'Color:' in parts[1] else 'color:')[1].strip()
                    
                    items.append({
                        'image': image_filename,
                        'type': type_part,
                        'color': color_part,
                        'raw_text': response_text,
                        'analysis_date': datetime.now()
                    })
                except:
                    continue
    
    return items

def save_to_csv(data, filename='ootd_data.csv'):
    """Save data to CSV file"""
    if not data:
        return
        
    fieldnames = ['image', 'type', 'color', 'analysis_date']
    
    file_exists = os.path.isfile(filename)
    
    try:
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            for item in data:
                # Only write required fields to CSV
                csv_item = {k: item[k] for k in fieldnames if k in item}
                writer.writerow(csv_item)
        logger.info(f"Data saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving to CSV: {str(e)}")

def save_to_mongodb(data):
    """Insert data into MongoDB with error handling"""
    if not data:
        return
        
    try:
        result = collection.insert_many(data)
        logger.info(f"Inserted {len(result.inserted_ids)} items into MongoDB")
        return result.inserted_ids
    except Exception as e:
        logger.error(f"Error saving to MongoDB: {str(e)}")
        return None

def process_ootd_images(image_folder, batch_size=10):
    """Process OOTD images in batches to manage memory and API rate limits"""
    if not os.path.exists(image_folder):
        logger.error(f"Image folder does not exist: {image_folder}")
        return
        
    # Get list of image files
    image_files = [f for f in os.listdir(image_folder) 
                  if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) 
                  and os.path.isfile(os.path.join(image_folder, f))]
    
    logger.info(f"Found {len(image_files)} images to process")
    
    all_data = []
    batch_count = 0
    
    # Process in batches
    for i in range(0, len(image_files), batch_size):
        batch = image_files[i:i+batch_size]
        batch_count += 1
        batch_data = []
        
        logger.info(f"Processing batch {batch_count} ({len(batch)} images)...")
        
        for filename in batch:
            image_path = os.path.join(image_folder, filename)
            logger.info(f"Processing {filename}...")
            
            try:
                # Analyze image
                response = analyze_ootd(image_path)
                if not response:
                    logger.warning(f"No response for {filename}, skipping")
                    continue
                    
                # Parse response
                parsed_data = parse_response(response, filename)
                batch_data.extend(parsed_data)
                
                logger.info(f"Found {len(parsed_data)} clothing items in {filename}")
                
                # Slight pause to respect API rate limits
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing {filename}: {str(e)}")
                continue
        
        # Save batch data to MongoDB
        if batch_data:
            save_to_mongodb(batch_data)
            all_data.extend(batch_data)
        
        # Save all data to CSV after each batch
        save_to_csv(all_data)
        
        # Pause between batches to respect API rate limits
        if i + batch_size < len(image_files):
            logger.info(f"Pausing between batches...")
            time.sleep(2)
    
    logger.info(f"Processing complete. Total items extracted: {len(all_data)}")
    return all_data

def get_stats_from_mongodb():
    """Get statistics about processed outfits"""
    try:
        # Most common clothing types
        pipeline_types = [
            {"$group": {"_id": "$type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        common_types = list(collection.aggregate(pipeline_types))
        
        # Most common colors
        pipeline_colors = [
            {"$group": {"_id": "$color", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        common_colors = list(collection.aggregate(pipeline_colors))
        
        # Most common color-type combinations
        pipeline_combos = [
            {"$group": {"_id": {"type": "$type", "color": "$color"}, "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        common_combos = list(collection.aggregate(pipeline_combos))
        
        stats = {
            "total_items": collection.count_documents({}),
            "total_images": len(collection.distinct("image")),
            "common_types": common_types,
            "common_colors": common_colors,
            "common_combinations": common_combos
        }
        
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return None

def setup_mongodb():
    """Initialize MongoDB with required indexes"""
    try:
        # Create indexes for faster queries
        collection.create_index("image")
        collection.create_index("type")
        collection.create_index("color")
        collection.create_index("analysis_date")
        logger.info("MongoDB indexes created successfully")
        return True
    except Exception as e:
        logger.error(f"Error setting up MongoDB: {str(e)}")
        return False

# Example usage
if __name__ == "__main__":
    # Setup MongoDB first
    if setup_mongodb():
        # Get image folder from environment or use default
        image_folder = os.getenv("IMAGE_FOLDER", "ootd_images")
        
        # Check if folder exists
        if not os.path.exists(image_folder):
            logger.warning(f"Image folder '{image_folder}' does not exist. Creating it...")
            try:
                os.makedirs(image_folder)
                logger.info(f"Created folder: {image_folder}")
                logger.info(f"Please add your OOTD images to this folder and run the script again.")
                exit(0)
            except Exception as e:
                logger.error(f"Failed to create folder: {str(e)}")
                exit(1)
        
        # Process images
        process_ootd_images(image_folder, batch_size=5)
        
        # Print stats
        stats = get_stats_from_mongodb()
        if stats:
            logger.info(f"Total items: {stats['total_items']}")
            logger.info(f"Total images: {stats['total_images']}")
            logger.info("Top clothing types:")
            for item in stats['common_types']:
                logger.info(f"  {item['_id']}: {item['count']}")