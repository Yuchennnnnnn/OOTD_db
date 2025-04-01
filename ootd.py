from pinterest_dl import PinterestDL

# Initialize and run the Pinterest image downloader with specified settings
images = PinterestDL.with_api(
    timeout=3,  # Timeout in seconds for each request (default: 3)
    verbose=False,  # Enable detailed logging for debugging (default: False)
).scrape_and_download(
    url="https://www.pinterest.com/pin/4610841686258872320/",  # Pinterest URL to scrape
    output_dir="images",  # Directory to save downloaded images
    limit=25  # Max number of images to download 
)