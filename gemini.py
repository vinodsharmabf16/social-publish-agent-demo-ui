# To run this code you need to install the following dependencies:
# pip install google-genai python-dotenv

import base64
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from datetime import datetime
import json

# Load environment variables
load_dotenv()

def generate(business_name: str, industry: str, sub_industry: str = None, location: str = None, date_time: str = None):
    """
    Generate trending topics based on business parameters.
    
    Args:
        business_name (str): Name of the business
        industry (str): Main industry of the business
        sub_industry (str, optional): Sub-industry specification
        location (str, optional): Business location
        date_time (str, optional): Target date and time (defaults to current time if not provided)
    """
    # Initialize the client with API key from .env file
    client = genai.Client(
        api_key=os.getenv("API_KEY"),
    )

    # Use current date time if not provided
    if date_time is None:
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Format the input for the model
    input_text = f"""Business Analysis Request:
Business Name: {business_name}
Industry: {industry}
Sub-Industry: {sub_industry if sub_industry else 'Not specified'}
Location: {location if location else 'Global'}
Date & Time: {date_time}

Please analyze trending topics for this business based on the provided parameters. Return ONLY valid JSON with no additional text."""

    model = "gemini-2.5-flash-preview-04-17"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=input_text),
            ],
        ),
    ]
    tools = [
        types.Tool(google_search=types.GoogleSearch()),
    ]
    generate_content_config = types.GenerateContentConfig(
        tools=tools,
        response_mime_type="text/plain",
        system_instruction=[
            types.Part.from_text(text="""You are a JSON-only response generator. Your task is to return ONLY valid JSON with no additional text or explanation.

Task: Identify trending topics that are emerging today, relevant to the business, and can be used for social media content.

Output Format:
{
  "trending_topics": [
    {
      "trend_name": "string (1–3 words max)",
      "trend_category": "Industry | Sub-Industry | Seasonal | Festival | Event | Meme | General Social Media",
      "date_time": "YYYY-MM-DDTHH:MM:SS",
      "post_ideas": [
        "string (short social media caption idea)",
        "string (optional second caption idea)",
        "string (optional third caption idea)"
      ],
      "source_type": "Twitter Trend | Google Trend | News | Social Media"
    }
  ]
}

Requirements:
1. Return ONLY valid JSON, no other text
2. Include a mix of trends from different categories
3. Topics must be suitable for business social media posts
4. No negative, political, or NSFW content
5. Must be brand-safe and visual-content friendly
6. Topics should be relevant for up to 1 month in the future
7. Each trend should have 2-3 post ideas
8. Use ISO 8601 format for dates (YYYY-MM-DDTHH:MM:SS)
9. MUST generate exactly 10 trending topics
10. Topics MUST be sorted in the following order:
    - First by business domain
    - Then by sub industry then followed by industry"""),
        ],
    )

    result = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        result += chunk.text

    # Clean and validate the JSON before outputting
    try:
        # Find the JSON content
        start_idx = result.find('{')
        end_idx = result.rfind('}') + 1
        if start_idx >= 0 and end_idx > start_idx:
            json_str = result[start_idx:end_idx]
            # Parse and re-serialize to ensure valid JSON
            parsed_json = json.loads(json_str)
            print(json.dumps(parsed_json, indent=2))
        else:
            print('{"trending_topics": []}')
    except json.JSONDecodeError:
        print('{"trending_topics": []}')

if __name__ == "__main__":
    # Example usage
    generate(
        business_name="Example Coffee Shop",
        industry="Food & Beverage",
        sub_industry="Coffee Shop",
        location="New York",
        # date_time parameter is optional, will use current time if not provided
    )
