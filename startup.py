import gradio as gr
import datetime
from dotenv import load_dotenv, set_key
from logger import get_logger

logger = get_logger(__name__)

def render_startup(continue_callback):
    logger.info("Rendering startup page.")
    gr.Markdown("### BirdAI will generate posts based on")
    sources = gr.CheckboxGroup(
        ["Your industry", "Holiday", "Your top performing posts", "Competitor's top performing posts", "Trending topics"],
        value=["Your industry", "Holiday", "Your top performing posts", "Competitor's top performing posts", "Trending topics"],
        label="",
        interactive=True
    )

    gr.Markdown("### Choose how many posts to generate each week")

    frequency = gr.Radio(
        ["Weekly", "Next 4 weeks"],
        value="Weekly",
        label="Frequency",
        interactive=True
    )

    posts_per_week = gr.Textbox(
        type="text",
        value="7",
        label="Posts per week",
        interactive=True
    )
    set_key(".env", "POSTS_PER_WEEK", "7")
    # Create a function to capture and print the posts per week value
    def update_posts_per_week(posts):
        logger.info(f"Posts per week updated to: {posts}")
        set_key(".env", "POSTS_PER_WEEK", posts)

    # Set the callback to execute when `posts_per_week` value changes
    posts_per_week.change(update_posts_per_week, inputs=posts_per_week)

    logger.info(f"Startup page rendered with default value -- Posts per week: {posts_per_week.value}")

