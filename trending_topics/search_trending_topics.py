import json
from openai import OpenAI
import openai


def get_trending_topics(
        business_name: str,
        industry: str,
        sub_industry: str,
        country: str,
        city: str,
        state: str,
        recency: int
):
    """
    Fetches trending topics relevant to a business using OpenAI's web search capability.

    Args:
        business_name: Name of the business
        industry: Primary industry of the business
        sub_industry: Sub-industry or niche
        country: Country code (e.g., "IN" for India)
        city: City name
        region: Region or state

    Returns:
        JSON response containing business info and trending topics
    """
    # Create OpenAI client
    client = OpenAI()

    # Construct the prompt
    prompt = f"""
    You're a trend analyst and social media strategist focused on identifying the buzz

    Based on the following business:
    - Business Name: {business_name}
    - Industry: {industry}
    - Sub-Industry: {sub_industry}
    - Location: {city}, {state}, {country}

    Return the top 20 trending topics relevant to this business that are suitable for social media posts, using trending data from last **{recency}** days only.

    Each topic must include:
    - "topic": A short, keyword-style phrase (1–2 words, like a hashtag but without `#`)
    - "description": 1–2 line explanation of the trend
    - "source": A credible URL that directly supports the topic and is published within or very close to the selected recency period last ({recency}) days
    - "social_post_idea": Short, engaging caption that could be posted on social media with some #hashtags

    Ensure:
    - All source links are relevant to the specific topic
    - The publication date of each source aligns closely with the last {recency} days window

    Format the response as JSON with the following structure:

    {{
      "business_name": "...",
      "industry": "...",
      "sub_industry": "...",
      "location": "...",
      "business_information": "...",
      "trending_topics": [
        {{
          "topic": "...",
          "description": "...",
          "source": "...",
          "social_post_idea": "..."
        }}
      ]
    }}
    """

    # Call OpenAI with web_search_preview tool
    response = client.responses.create(
        model="gpt-4.1-mini",
        tools=[{
            "type": "web_search_preview_2025_03_11",
            "search_context_size": "high",
            "user_location": {
                "type": "approximate",
                "country": country,
                "city": city,
                "region": state,
            }
        }],
        input=[
            {"role": "user", "content": prompt}
        ]
    )

    # Extract JSON from response
    result_text = response.output_text

    # Clean the response if it contains markdown code blocks
    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0].strip()
    elif "```" in result_text:
        result_text = result_text.split("```")[1].split("```")[0].strip()

    # Parse the JSON
    try:
        result_json = json.loads(result_text)
        return result_json
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON response", "raw_response": result_text}


def analyze_and_prioritize_topics(business_data, temperature=0.1):
    """
    Analyzes and prioritizes trending topics for maximum business impact.

    Args:
        business_data: JSON data with business info and trending topics
        model: OpenAI model to use for analysis
        temperature: Temperature setting for response creativity

    Returns:
        JSON string with prioritized topics and analysis
    """
    # Convert trending topics to text format for the prompt
    topics_text = ""
    for i, topic in enumerate(business_data.get("trending_topics", [])):
        topics_text += f"\nTopic {i + 1}: {topic['topic']}\n"
        topics_text += f"Description: {topic['description']}\n"
        topics_text += f"Source: {topic['source']}\n"
        topics_text += f"Sample Post Idea: {topic['social_post_idea']}\n"

    system_prompt = f"""
    I need you to analyze trending topics for a business and identify the most strategic ones for social media marketing.

    BUSINESS INFORMATION:
    - Business Name: {business_data.get('business_name')}
    - Industry: {business_data.get('industry')}
    - Sub-Industry: {business_data.get('sub_industry')}
    - Location: {business_data.get('location')}
    - Business Description: {business_data.get('business_information')}

    TRENDING TOPICS:
    {topics_text}

    Your task:

    1. ANALYZE each topic based on:
       - Market potential (customer demand and growth trajectory)
       - Relevance to the specific business
       - Potential for customer engagement
       - Competitive advantage opportunity
       - Alignment with current consumer behavior
       - Positive sentiment potential

    2. SELECT the top 10 most strategic topics that would genuinely drive customer interest and business growth

    3. RANK them from most to least impactful

    4. EXPLAIN your strategic reasoning for each selection

    5. IDENTIFY which topics you're specifically NOT recommending and why

    IMPORTANT: Return your analysis as a valid JSON object with the following structure:
    {{
        "business_information": {{
            "business_name": "...",
            "industry": "...",
            "sub_industry": "...",
            "location": "...", 
            "description": "..."
        }},
        "selected_topics": [
            {{
                "rank": 1,
                "topic": "...",
                "description": "...",
                "source": "...",
                "social_post_idea": "...",
                "strategic_reasoning": "..."
            }}
        ],
        "rejected_topics": [
            {{
                "topic": "...",
                "rejection_reason": "..."
            }}
        ]
    }}
    Make sure the JSON is properly formatted and can be parsed.
    """

    user_prompt = "You are an expert in strategic marketing and business growth. Think deeply about which trending topics would actually drive customer interest and business growth. Focus on genuine business impact, not just social media engagement."

    try:
        # Message content
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=temperature
        )

        # Extract the response
        result_text = response.choices[0].message.content.strip()

        # Clean the response if it contains markdown code blocks
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        # Parse the JSON
        try:
            result_json = json.loads(result_text)
            return result_json
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON response", "raw_response": result_text}
    except Exception as e:
        return {"error": f"API call error: {str(e)}"}


def generate_social_media_strategy(
        business_name: str,
        industry: str,
        sub_industry: str,
        country: str,
        city: str,
        state: str,
        recency: int,
):
    """
    End-to-end function that gets trending topics and analyzes them for a comprehensive
    social media strategy.

    Args:
        business_name: Name of the business
        industry: Primary industry of the business
        sub_industry: Sub-industry or niche
        country: Country code (e.g., "IN" for India)
        city: City name
        region: Region or state
        model: OpenAI model to use for analysis

    Returns:
        Dictionary with complete social media strategy analysis
    """
    # Step 1: Get trending topics
    trending_data = get_trending_topics(
        business_name=business_name,
        industry=industry,
        sub_industry=sub_industry,
        country=country,
        city=city,
        state=state,
        recency=recency
    )
    if "error" in trending_data:
        return trending_data

    # Step 2: Analyze and prioritize topics
    analysis_results = analyze_and_prioritize_topics(
        business_data=trending_data
    )

    return analysis_results

# # Example usage
# if __name__ == "__main__":
#     result = generate_social_media_strategy(
#         business_name="Reliance Industries",
#         industry="Retail",
#         sub_industry="Retail",
#         country="IN",
#         city="Mumbai",
#         region="Maharashtra",
#         recency="This Month" # This will take 3 types [This week, This Month (default), This Quarter]
#     )
#
#     # Print the result in a formatted way
#     print(json.dumps(result, indent=2))
