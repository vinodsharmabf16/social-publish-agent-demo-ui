import gradio as gr
import datetime

def render_startup(continue_callback):
    gr.Markdown("### BirdAI will generate posts based on")
    sources = gr.CheckboxGroup(
        ["Your industry", "Holiday", "Your top performing posts" , "Competitor's top performing posts", "Trending topics"],
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
