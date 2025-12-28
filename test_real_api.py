import os
import requests
from decouple import config

# 1. Setup configuration
BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/api/drug/check/"
IMAGE_PATH = "test_drug.jpg"  # Make sure this file exists!

def test_real_drug_check():
    print(f"Testing API at: {API_URL}")
    
    # Check if image exists
    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Image file '{IMAGE_PATH}' not found.")
        print("Please place a valid image of a drug (e.g., Ibuprofen, Paracetamol) in this directory.")
        return

    # 2. Prepare the payload
    payload = {
        "symptoms": "Severe headache and fever"
    }
    
    # 3. Send the request
    try:
        with open(IMAGE_PATH, "rb") as img_file:
            files = {
                "drug_image": (IMAGE_PATH, img_file, "image/jpeg")
            }
            
            print("Sending request... (this may take a few seconds)")
            response = requests.post(API_URL, data=payload, files=files)
            
        # 4. Print results
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n--- Analysis Result ---")
            print(f"Drug Identified: {data.get('drug_identified')}")
            print(f"Suitable: {data.get('is_suitable')}")
            print(f"Confidence: {data.get('confidence')}")
            print(f"Explanation: {data.get('explanation')}")
        else:
            print("\n--- Error ---")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the server.")
        print("Make sure the Django server is running: `python manage.py runserver`")

if __name__ == "__main__":
    # Ensure requests is installed
    try:
        import requests
    except ImportError:
        print("Installing requests library...")
        os.system("pip install requests")
        import requests

    test_real_drug_check()
