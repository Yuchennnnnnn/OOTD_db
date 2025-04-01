# OOTD Analyzer

The **OOTD Analyzer** is a Python-based project that analyzes outfit images (OOTD – Outfit Of The Day) and stores detailed clothing information (e.g., type and color) in a MongoDB database. The project also supports text-based image search and an advanced matching feature that accepts a user-uploaded photo, searches for similar items in the database, and uses AI to explain the match based on style, color, or pattern.

## Features

- **Image Analysis:**  
  Processes images of outfits using an AI API to extract specific clothing details such as type and color.

- **Data Storage:**  
  Stores the analysis results in a MongoDB database for later retrieval and analysis.

- **Text-Based Image Search:**  
  Allows users to input a text prompt (e.g., "Show me an OOTD featuring green sneakers") to retrieve the most relevant image from the database.


## Prerequisites

- **Python 3.10+**
- **MongoDB:** Ensure MongoDB is installed and running on your machine (default URI: `mongodb://localhost:27017/`).
- **Pip Packages:** Install required Python packages using pip:
  ```bash
  pip install pymongo python-dotenv pillow matplotlib openai
  ```

## Setup Instructions

1. **Download the Repository:**
   Download the project files to your local machine.

2. **Environment Variables (.env):**  
   The project uses environment variables to store configuration settings. A sample `.env` file is automatically created when you run `setup_mongodb.py` if one does not exist. Edit the `.env` file to set your values:
   - `OPENROUTER_API_KEY`: Your OpenRouter (or OpenAI) API key.
   - `MONGO_URI`: MongoDB connection string (default: `mongodb://localhost:27017/`).
   - `DB_NAME`: Database name (default: `ootd_database`).
   - `COLLECTION_NAME`: Collection name (default: `outfits`).
   - `IMAGE_FOLDER`: Folder where outfit images are stored (default: `images`).
   - `SITE_NAME`: (Optional) Site name for logging/headers.

3. **Setup MongoDB:**  
   Run the setup script to initialize your MongoDB database and create required indexes:
   ```bash
   python setup_mongodb.py
   ```

4. **Add Your Outfit Images:**  
  Run the setup script to download photos, you can change the link in the script:
   ```bash
   python ootd.py
   ```
   Place your outfit images into the folder specified by the `IMAGE_FOLDER` environment variable (default: './images'). Ensure the images are in one of these formats: `.jpg`, `.jpeg`, `.png`, or `.webp`.

## How to Use

### 1. Analyzing Outfit Images

Run the main analysis script to process your outfit images:
```bash
python ootd_analyzer.py
```

### 2. Text-Based Image Search

To search for an outfit using a text prompt:
```bash
python text_search.py
```



## Project Files Overview

- **setup_mongodb.py**
- **ootd_analyzer.py**
- **text_search.py**
- **ootd_data.csv**
- **ootd_processing.log**

## Acknowledgements

- [MongoDB](https://www.mongodb.com/)
- [OpenRouter API](https://openrouter.ai/) or [OpenAI](https://openai.com/)
- Python libraries: pymongo, python-dotenv, Pillow, matplotlib