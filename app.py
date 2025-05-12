import gradio as gr
from pages import outcomes, trigger, tasks

def render():
    with gr.Blocks(title="Social Publishing Agent", theme=gr.themes.Default(primary_hue="blue")) as demo:
        gr.Markdown("##  Social publishing agent", elem_id="main-header")

        with gr.Tabs():
            with gr.Tab("Outcomes"):
                outcomes.render()
            with gr.Tab("Trigger"):
                trigger.render()
            with gr.Tab("Tasks"):
                tasks.render()
    return demo

if __name__ == "__main__":
    render().launch()
