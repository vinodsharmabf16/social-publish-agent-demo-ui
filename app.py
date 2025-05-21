import streamlit as st
import json
from datetime import datetime
from gemini import generate

st.set_page_config(
    page_title="Trending Topics Generator",
    page_icon="📈",
    layout="wide"
)

# Add custom CSS
st.markdown("""
<style>
.trend-card {
    padding: 20px;
    border-radius: 10px;
    background-color: #f0f2f6;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.trend-card h3 {
    color: #1f1f1f;
    margin-bottom: 15px;
    font-size: 1.2em;
}
.trend-info {
    margin-bottom: 15px;
    color: #424242;
}
.trend-info p {
    margin: 5px 0;
}
.post-ideas-container {
    background-color: white;
    border-radius: 8px;
    padding: 10px;
    margin-top: 10px;
}
.post-idea {
    padding: 12px;
    background-color: #ffffff;
    border-left: 4px solid #2e7dff;
    border-radius: 0 8px 8px 0;
    margin: 8px 0;
    font-size: 0.95em;
    color: #2c3e50;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.post-idea:hover {
    background-color: #f8f9fa;
    transition: background-color 0.2s ease;
}
.category-badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 0.85em;
    font-weight: 500;
    background-color: #e3f2fd;
    color: #1976d2;
    margin-bottom: 10px;
}
.source-badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 0.85em;
    font-weight: 500;
    background-color: #f3e5f5;
    color: #7b1fa2;
    margin-left: 8px;
}
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("📈 Trending Topics Generator")
st.markdown("Generate trending topics for your business's social media content.")

# Create two columns for input
col1, col2 = st.columns(2)

with col1:
    business_name = st.text_input("Business Name*", placeholder="Enter your business name")
    industry = st.text_input("Industry*", placeholder="e.g., Food & Beverage")
    sub_industry = st.text_input("Sub-Industry (Optional)", placeholder="e.g., Coffee Shop")

with col2:
    location = st.text_input("Location (Optional)", placeholder="e.g., New York")
    use_current_time = st.checkbox("Use current date/time", value=True)
    if not use_current_time:
        date_time = st.text_input(
            "Date & Time (Optional)", 
            placeholder="YYYY-MM-DD HH:MM:SS",
            help="Leave empty to use current time"
        )
    else:
        date_time = None

# Generate button
if st.button("Generate Trending Topics", type="primary", disabled=not (business_name and industry)):
    if not business_name or not industry:
        st.error("Please provide both Business Name and Industry.")
    else:
        try:
            with st.spinner("Generating trending topics..."):
                # Capture the output in a string
                import io
                import sys
                output = io.StringIO()
                sys.stdout = output
                
                # Call generate function
                generate(
                    business_name=business_name,
                    industry=industry,
                    sub_industry=sub_industry if sub_industry else None,
                    location=location if location else None,
                    date_time=date_time if not use_current_time and date_time else None
                )
                
                # Restore stdout
                sys.stdout = sys.__stdout__
                
                # Get the output and parse as JSON
                result = output.getvalue().strip()
                
                try:
                    # Try to find JSON content in the output
                    start_idx = result.find('{')
                    end_idx = result.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = result[start_idx:end_idx]
                        data = json.loads(json_str)
                        
                        if "trending_topics" in data and isinstance(data["trending_topics"], list):
                            # Display results in a grid
                            st.subheader("📊 Generated Trending Topics")
                            
                            # Create a grid of cards
                            cols = st.columns(2)
                            for i, topic in enumerate(data["trending_topics"]):
                                with cols[i % 2]:
                                    with st.container():
                                        st.markdown(f"""
                                        <div class="trend-card">
                                            <h3>#{i+1} {topic['trend_name']}</h3>
                                            <div class="trend-info">
                                                <span class="category-badge">{topic['trend_category']}</span>
                                                <span class="source-badge">{topic['source_type']}</span>
                                                <p><strong>Date:</strong> {topic['date_time']}</p>
                                            </div>
                                            <div class="post-ideas-container">
                                                <strong>📝 Post Ideas:</strong>
                                                {''.join([f'<div class="post-idea">{idea}</div>' for idea in topic['post_ideas']])}
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                        else:
                            st.error("Invalid JSON structure: Missing 'trending_topics' array")
                            st.code(result)
                    else:
                        st.error("No valid JSON found in the output")
                        st.code(result)
                
                except json.JSONDecodeError as e:
                    st.error(f"Failed to parse JSON: {str(e)}")
                    st.code(result)
                except Exception as e:
                    st.error(f"An error occurred while processing the results: {str(e)}")
                    st.code(result)
                
        except Exception as e:
            st.error(f"An error occurred during generation: {str(e)}")

# Add footer with instructions
st.markdown("---")
st.markdown("""
### How to use:
1. Enter your business name and industry (required)
2. Optionally provide sub-industry and location for more targeted results
3. Choose whether to use current time or specify a custom date/time
4. Click "Generate Trending Topics" to get your results

The tool will generate trending topics relevant to your business, complete with post ideas and categorization.
""") 