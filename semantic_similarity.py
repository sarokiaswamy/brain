# Import prerequisite libraries
import os
import numpy as np
from openai import OpenAI
import PyPDF2
import docx
import time
from typing import List, Dict, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class GeminiSettings:
    """Settings for Gemini model connections."""
    
    API_KEY: str = os.getenv("GEMINI_API_KEY", "").rstrip('%')
    BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/"
    MODEL_NAME: str = "gemini-2.0-flash-lite-001"
    EMBEDDING_MODEL: str = "models/embedding-001"
    MAX_RETRIES: int = 3
    SLEEP_TIME: int = 30

gemini_settings = GeminiSettings()

def get_client() -> OpenAI:
    """Get Gemini client with API key."""
    return OpenAI(
        api_key=gemini_settings.API_KEY,
        base_url=gemini_settings.BASE_URL
    )

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text content from a PDF file."""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
    except Exception as e:
        print(f"Error extracting text from PDF {file_path}: {str(e)}")
        return ""

def extract_text_from_docx(file_path: str) -> str:
    """Extract text content from a DOCX file."""
    try:
        doc = docx.Document(file_path)
        text = '\n'.join([para.text for para in doc.paragraphs if para.text])
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX {file_path}: {str(e)}")
        return ""

def get_file_text(file_path: str) -> str:
    """Get text content from a file based on its extension."""
    if file_path.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.lower().endswith('.docx'):
        return extract_text_from_docx(file_path)
    else:
        print(f"Unsupported file format: {file_path}")
        return ""

def get_embedding(client: OpenAI, text: str) -> List[float]:
    """Get embedding for a text using the Gemini model."""
    try:
        # Truncate text if too long (adjust max_length as needed)
        # max_length = 8000
        # if len(text) > max_length:
        #     text = text[:max_length]
            
        response = client.embeddings.create(
            input=text,
            model=gemini_settings.EMBEDDING_MODEL
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {str(e)}")
        # Return a zero vector as fallback
        return [0.0] * 768  # Assuming embedding dimension is 768 for Gemini

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def main():
    """Main function to analyze semantic similarity between files."""
    # Paths to directories - using environment variables with fallbacks
    requirements_dir = os.getenv('REQUIREMENTS_DIR', './Requirements(Input)')
    responses_dir = os.getenv('RESPONSES_DIR', './Responses')
    
    # Initialize Gemini client
    print("Initializing Gemini client...")
    client = get_client()
    
    # Get all files in the directories
    requirements_files = [f for f in os.listdir(requirements_dir) 
                         if os.path.isfile(os.path.join(requirements_dir, f)) and 
                         (f.lower().endswith('.pdf') or f.lower().endswith('.docx'))]
    
    responses_files = [f for f in os.listdir(responses_dir) 
                      if os.path.isfile(os.path.join(responses_dir, f)) and 
                      (f.lower().endswith('.pdf') or f.lower().endswith('.docx'))]
    
    print(f"Found {len(requirements_files)} files in Requirements directory")
    print(f"Found {len(responses_files)} files in Responses directory")
    
    # Process each file in the Requirements directory
    results = []
    
    for req_file in requirements_files:
        req_path = os.path.join(requirements_dir, req_file)
        print(f"\nProcessing requirement file: {req_file}")
        
        # Extract text from the requirement file
        req_text = get_file_text(req_path)
        if not req_text:
            print(f"Could not extract text from {req_file}, skipping...")
            continue
            
        print(f"Extracted {len(req_text)} characters from {req_file}")
        
        # Get embedding for the requirement file
        print(f"Getting embedding for {req_file}...")
        req_embedding = get_embedding(client, req_text)
        
        # Compare with each file in the Responses directory
        file_similarities = []
        
        for res_file in responses_files:
            res_path = os.path.join(responses_dir, res_file)
            print(f"Processing response file: {res_file}")
            
            # Extract text from the response file
            res_text = get_file_text(res_path)
            if not res_text:
                print(f"Could not extract text from {res_file}, skipping...")
                continue
                
            print(f"Extracted {len(res_text)} characters from {res_file}")
            
            # Get embedding for the response file
            print(f"Getting embedding for {res_file}...")
            res_embedding = get_embedding(client, res_text)
            
            # Calculate similarity
            similarity = cosine_similarity(req_embedding, res_embedding)
            file_similarities.append((res_file, similarity))
            print(f"Similarity between {req_file} and {res_file}: {similarity:.4f}")
            
            # Add a small delay to avoid rate limiting
            time.sleep(1)
        
        # Sort by similarity (highest first)
        file_similarities.sort(key=lambda x: x[1], reverse=True)
        results.append((req_file, file_similarities))
    
    # Print final results
    print("\n\n===== FINAL RESULTS =====")
    for req_file, similarities in results:
        print(f"\nRequirement file: {req_file}")
        print("Matching response files (in order of similarity):")
        for i, (res_file, similarity) in enumerate(similarities[:5], 1):
            print(f"{i}. {res_file} - Similarity: {similarity:.4f}")
    
    # Write results to a file
    output_file = os.path.join(os.path.dirname(requirements_dir), "similarity_results.txt")
    with open(output_file, "w") as f:
        f.write("Semantic Similarity Analysis Results\n")
        f.write("===================================\n\n")
        
        for req_file, similarities in results:
            f.write(f"Requirement file: {req_file}\n")
            f.write("Matching response files (in order of similarity):\n")
            for i, (res_file, similarity) in enumerate(similarities, 1):
                f.write(f"{i}. {res_file} - Similarity: {similarity:.4f}\n")
            f.write("\n")
    
    print(f"\nResults written to {output_file}")

if __name__ == "__main__":
    main()
