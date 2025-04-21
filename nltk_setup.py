import nltk
import os

def setup_nltk():
    """Download required NLTK data if not already present."""
    # Create a directory for NLTK data if it doesn't exist
    nltk_data_dir = os.path.expanduser('~/nltk_data')
    if not os.path.exists(nltk_data_dir):
        os.makedirs(nltk_data_dir)
    
    # Check if required NLTK data is already downloaded
    required_data = {
        'tokenizers/punkt': 'punkt',
        'corpora/stopwords': 'stopwords'
    }
    
    for data_path, data_name in required_data.items():
        if not os.path.exists(os.path.join(nltk_data_dir, data_path)):
            nltk.download(data_name, quiet=True)
