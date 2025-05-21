import streamlit as st
import json
import time
from openai import OpenAI
import os
import openai


# Set page configuration
st.set_page_config(
    page_title="Trending Generator",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem !important;
        color: #1E88E5;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-bottom: 1rem;
    }
    .result-section {
        background-color: #f5f5f5;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .stProgress > div > div > div > div {
        background-color: #1E88E5;
    }
</style>
""", unsafe_allow_html=True)


def get_trending_topics(
        business_name: str,
        industry: str,
        sub_industry: str,
        country: str,
        city: str,
        region: str,
        recency: str
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
    - Location: {city}, {region}, {country}

    Return the top 20 trending topics relevant to this business that are suitable for social media posts, using trending data from **{recency}** only.

    Each topic must include:
    - "topic": A short, keyword-style phrase (1–2 words, like a hashtag but without `#`)
    - "description": 1–2 line explanation of the trend
    - "source": A credible URL that directly supports the topic and is published within or very close to the selected recency period ({recency})
    - "social_post_idea": Short, engaging caption that could be posted on social media with some #hashtags
    
    Ensure:
    - All source links are relevant to the specific topic
    - The publication date of each source aligns closely with the {recency} window

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
                "region": region,
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


def analyze_and_prioritize_topics(business_data, model="gpt-4o", temperature=0.1):
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
            model=model,
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


def display_trending_data(trending_data):
    """Helper function to display trending data in a nice format"""
    if "error" in trending_data:
        st.error(f"Error retrieving trending topics: {trending_data['error']}")
        if "raw_response" in trending_data:
            st.text(trending_data["raw_response"])
        return

    st.subheader("Business Information", divider="blue")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Business Name:** {trending_data.get('business_name', 'N/A')}")
        st.write(f"**Industry:** {trending_data.get('industry', 'N/A')}")
        st.write(f"**Sub-Industry:** {trending_data.get('sub_industry', 'N/A')}")
    with col2:
        st.write(f"**Location:** {trending_data.get('location', 'N/A')}")
        st.write(f"**Description:** {trending_data.get('business_information', 'N/A')}")

    st.subheader("Trending Topics", divider="blue")

    # Check if trending_topics exists and is not empty
    trending_topics = trending_data.get("trending_topics", [])
    if not trending_topics:
        st.warning("No trending topics found.")
        return

    # Create tabs for different views
    tab1, tab2 = st.tabs(["Card View", "Table View"])

    with tab1:
        # Card view - 3 columns
        rows = [trending_topics[i:i + 3] for i in range(0, len(trending_topics), 3)]
        for row in rows:
            cols = st.columns(3)
            for i, topic in enumerate(row):
                with cols[i]:
                    st.markdown(f"### {topic.get('topic', 'N/A')}")
                    st.markdown(f"**Description:** {topic.get('description', 'N/A')}")

                    source = topic.get('source', 'N/A')
                    if source.startswith('http'):
                        st.markdown(f"**Source:** [Link]({source})")
                    else:
                        st.markdown(f"**Source:** {source}")

                    st.markdown(f"**Social Post Idea:** {topic.get('social_post_idea', 'N/A')}")
                    st.divider()

    with tab2:
        # Table view
        table_data = []
        for topic in trending_topics:
            table_data.append({
                "Topic": topic.get("topic", "N/A"),
                "Description": topic.get("description", "N/A"),
                "Social Post Idea": topic.get("social_post_idea", "N/A")
            })

        st.dataframe(table_data, use_container_width=True)


def display_analysis_results(analysis_results):
    """Helper function to display analysis results in a nice format"""
    if "error" in analysis_results:
        st.error(f"Error analyzing trending topics: {analysis_results['error']}")
        if "raw_response" in analysis_results:
            st.text(analysis_results["raw_response"])
        return

    # Business information
    business_info = analysis_results.get("business_information", {})
    st.subheader("Business Analysis", divider="blue")
    st.write(f"**Business:** {business_info.get('business_name', 'N/A')}")
    st.write(f"**Industry:** {business_info.get('industry', 'N/A')} / {business_info.get('sub_industry', 'N/A')}")
    st.write(f"**Location:** {business_info.get('location', 'N/A')}")
    st.write(f"**Description:** {business_info.get('description', 'N/A')}")

    # Selected topics
    st.subheader("Recommended Topics", divider="blue")
    selected_topics = analysis_results.get("selected_topics", [])

    if not selected_topics:
        st.warning("No recommended topics found.")
    else:
        # Create tabs for different views
        tab1, tab2 = st.tabs(["Detailed View", "Summary View"])

        with tab1:
            for topic in selected_topics:
                with st.expander(f"Rank {topic.get('rank', 'N/A')}: {topic.get('topic', 'N/A')}"):
                    st.markdown(f"**Description:** {topic.get('description', 'N/A')}")

                    source = topic.get('source', 'N/A')
                    if source.startswith('http'):
                        st.markdown(f"**Source:** [Link]({source})")
                    else:
                        st.markdown(f"**Source:** {source}")

                    st.markdown(f"**Social Post Idea:** {topic.get('social_post_idea', 'N/A')}")
                    st.markdown(f"**Strategic Reasoning:** {topic.get('strategic_reasoning', 'N/A')}")

        with tab2:
            table_data = []
            for topic in selected_topics:
                table_data.append({
                    "Rank": topic.get("rank", "N/A"),
                    "Topic": topic.get("topic", "N/A"),
                    "Strategic Reasoning": topic.get("strategic_reasoning", "N/A")[:100] + "..." if len(
                        topic.get("strategic_reasoning", "")) > 100 else topic.get("strategic_reasoning", "N/A")
                })

            st.dataframe(table_data, use_container_width=True)

    # Rejected topics
    st.subheader("Rejected Topics", divider="blue")
    rejected_topics = analysis_results.get("rejected_topics", [])

    if not rejected_topics:
        st.info("No rejected topics found.")
    else:
        for topic in rejected_topics:
            with st.expander(f"{topic.get('topic', 'N/A')}"):
                st.markdown(f"**Rejection Reason:** {topic.get('rejection_reason', 'N/A')}")


# Streamlit app layout
def main():
    st.markdown("<h1 class='main-header'>Social Media Strategy Generator</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Generate trending topics and strategic recommendations for your business</p>",
                unsafe_allow_html=True)

    # API Key setup
    with st.sidebar:
        st.header("API Configuration")
        api_key = st.text_input("OpenAI API Key", type="password",
                                help="Enter your OpenAI API key. This key is required to use the OpenAI API.")

        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            st.success("API Key set!")

        st.markdown("---")
        st.write("Make sure your OpenAI API key has access to:")
        st.write("- GPT-4.1-mini (for trending topics)")
        st.write("- GPT-4o (for analysis)")
        st.write("- Web search capability")

        st.markdown("---")
        model_selection = st.selectbox("Analysis Model",
                                       ["gpt-4o", "gpt-4", "gpt-3.5-turbo"],
                                       index=0,
                                       help="Select the model to use for analyzing the trending topics")

    # User input section
    st.subheader("Business Information", divider="blue")

    col1, col2 = st.columns(2)
    with col1:
        business_name = st.text_input("Business Name", "Reliance Industries")
        industry = st.text_input("Industry", "Retail")
        sub_industry = st.text_input("Sub-Industry", "Retail")

    with col2:
        country = st.text_input("Country Code", "IN",
                                help="Two-letter country code (e.g., IN for India, US for United States)")
        city = st.text_input("City", "Hyderabad")
        region = st.text_input("Region/State", "Hyderabad")

    # Add recency selection dropdown
    recency = st.selectbox(
        "Trending Data Timeframe",
        ["Today", "This Week", "This Month", "This Quarter"],
        index=1,  # Default to "This Week"
        help="Select the timeframe for trending topics to analyze"
    )

    # Submit button
    generate_button = st.button("Generate Strategy", type="primary", use_container_width=True)

    if generate_button:
        # Check if API key is provided
        if not os.environ.get("OPENAI_API_KEY") and not st.secrets.get("OPENAI_API_KEY"):
            st.error("Please provide an OpenAI API key in the sidebar.")
            return

        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        # First step - Get trending topics
        status_text.text("Step 1/2: Fetching trending topics...")
        trending_data = get_trending_topics(
            business_name=business_name,
            industry=industry,
            sub_industry=sub_industry,
            country=country,
            city=city,
            region=region,
            recency=recency
        )
        progress_bar.progress(50)

        # Check if there's an error
        if "error" in trending_data:
            progress_bar.progress(100)
            status_text.text("Process completed with errors.")
            st.error(f"Error: {trending_data['error']}")
            if "raw_response" in trending_data:
                st.text(trending_data["raw_response"])
            return

        # Display trending topics
        st.markdown("<div class='result-section'>", unsafe_allow_html=True)
        st.markdown("## 📈 Trending Topics")
        display_trending_data(trending_data)
        st.markdown("</div>", unsafe_allow_html=True)

        # Second step - Analyze and prioritize topics
        status_text.text("Step 2/2: Analyzing and prioritizing topics...")
        analysis_results = analyze_and_prioritize_topics(
            business_data=trending_data,
            model=model_selection
        )
        progress_bar.progress(100)
        status_text.text("Process completed successfully!")

        # Display analysis results
        st.markdown("<div class='result-section'>", unsafe_allow_html=True)
        st.markdown("## 🔍 Analysis Results")
        display_analysis_results(analysis_results)
        st.markdown("</div>", unsafe_allow_html=True)

        # Add download buttons for JSON data
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Download Trending Topics (JSON)",
                data=json.dumps(trending_data, indent=2),
                file_name=f"{business_name}_trending_topics.json",
                mime="application/json"
            )
        with col2:
            st.download_button(
                label="Download Analysis Results (JSON)",
                data=json.dumps(analysis_results, indent=2),
                file_name=f"{business_name}_analysis_results.json",
                mime="application/json"
            )


if __name__ == "__main__":
    main()