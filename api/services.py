import json
import PIL.Image
from django.conf import settings
from decouple import config

class DrugValidityService:
    def analyze(self, drug_image, symptoms):
        try:
            from google import genai
        except ImportError:
            return {
                "error": "Google GenAI library is not installed. Please install it with `pip install google-genai`."
            }

        api_key = config("GEMINI_API_KEY")
        if not api_key:
            return {
                "error": "GEMINI_API_KEY is not set in settings."
            }

        client = genai.Client(api_key=api_key)

        try:
            # Open the image using PIL
            img = PIL.Image.open(drug_image)
        except Exception as e:
            return {"error": f"Failed to process image: {str(e)}"}

        prompt = (
            f"Analyze the image of the drug and determine if it is suitable for the following symptoms: '{symptoms}'. "
            "Identify the drug from the image first. "
            "Return a raw JSON response (no markdown formatting) with the following keys: "
            "'drug_identified' (string, name of the drug found), "
            "'is_suitable' (boolean), "
            "'confidence' (float between 0 and 1), "
            "and 'explanation' (string explaining the reasoning)."
        )

        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[prompt, img]
            )
            
            text_content = response.text
            
            # Clean up markdown code blocks if present
            if text_content.startswith("```json"):
                text_content = text_content[7:]
            if text_content.startswith("```"):
                text_content = text_content[3:]
            if text_content.endswith("```"):
                text_content = text_content[:-3]
                
            return json.loads(text_content.strip())
        except Exception as e:
            return {"error": str(e)}


class DrugAuthenticationService:
    def authenticate(self, drug_image):
        try:
            from google import genai
        except ImportError:
            return {
                "error": "Google GenAI library is not installed. Please install it with `pip install google-genai`."
            }

        api_key = config("GEMINI_API_KEY")
        if not api_key:
            return {
                "error": "GEMINI_API_KEY is not set in settings."
            }

        client = genai.Client(api_key=api_key)

        try:
            # Open the image using PIL
            img = PIL.Image.open(drug_image)
        except Exception as e:
            return {"error": f"Failed to process image: {str(e)}"}

        prompt = (
            "Analyze this image of a drug packaging or pill. "
            "Check for visual indicators of authenticity or counterfeiting (e.g., packaging quality, spelling errors, logo consistency, pill texture). "
            "Identify the drug from the image first. "
            "Return a raw JSON response (no markdown formatting) with the following keys: "
            "'drug_identified' (string, name of the drug found), "
            "'is_authentic' (boolean, true if it appears authentic, false if suspicious), "
            "'confidence' (float between 0 and 1), "
            "and 'explanation' (string explaining the reasoning)."
        )

        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[prompt, img]
            )
            
            text_content = response.text
            
            # Clean up markdown code blocks if present
            if text_content.startswith("```json"):
                text_content = text_content[7:]
            if text_content.startswith("```"):
                text_content = text_content[3:]
            if text_content.endswith("```"):
                text_content = text_content[:-3]
                
            return json.loads(text_content.strip())
        except Exception as e:
            return {"error": str(e)}
