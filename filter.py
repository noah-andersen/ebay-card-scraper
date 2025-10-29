import pandas as pd
import os

# Get project root directory
root = os.path.dirname(os.path.abspath(__file__))

def base_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply base filtering to the DataFrame.
    This function can be expanded with actual filtering logic as needed.
    """

    # Check for the correct column names
    columns = df.columns.tolist()
    expected_columns = ['title', 'card_name', 'grading_company', 'grade', 'price', 'listing_url', 'listing_id', 'image_urls', 'source', 'scraped_date', 'images']
    if columns != expected_columns:
        raise ValueError(f"DataFrame columns do not match expected columns. Found: {columns}")
    
    # Inital number of ebay card listings
    start_listing_count = len(df)
    
    # Find rows that have either no images or one image in the 'images' column - take the file path and delete the images
    # Then remove the rows from the DataFrame
    rows_to_remove = []
    for index, row in df.iterrows():
        images = row['images']
        if not images or len(images) <= 1:
            # Delete image files if they exist
            for img_path in images:
                if os.path.exists(img_path):
                    os.remove(img_path)
            rows_to_remove.append(index)