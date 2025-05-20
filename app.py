import gradio as gr
from pages import outcomes, tasks, output, flow
from startup import render_startup
from logger import get_logger

logger = get_logger(__name__)

def render():
    #logger.info("Rendering main Gradio app UI.")
    with gr.Blocks(title="Social Publishing Agent", theme=gr.themes.Default(primary_hue="blue")) as demo:
        gr.Markdown("## Social publishing agent", elem_id="main-header")

        # === App State ===
        show_main_app = gr.State(False)

        # === Startup Screen ===
        with gr.Column(visible=True) as startup_screen:
            #logger.info("Rendering startup screen.")
            render_startup(
                continue_callback=lambda sources, freq, posts: (
                    gr.update(visible=False),  # Hide startup
                    gr.update(visible=True)   # Show tabs
                )
            )
            continue_btn = gr.Button("Continue")

        # === Main App (tabs) ===
        with gr.Tabs(visible=False) as main_tabs:
            with gr.Tab("Outcomes"):
                #logger.info("Rendering Outcomes tab.")
                outcomes.render()
            with gr.Tab("Tasks"):
                #logger.info("Rendering Tasks tab.")
                tasks.render(on_publish=lambda: gr.update(visible=True))  # Use gr.update to show Output tab
            with gr.Tab("Output", visible=True) as output_tab:  
                #logger.info("Rendering Output tab.")
                output.render()
            with gr.Tab("Flow"):
                #logger.info("Rendering Flow tab.")
                flow.render()

        continue_btn.click(
            fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
            outputs=[startup_screen, main_tabs]
        )

    return demo

if __name__ == "__main__":
    #logger.info("Launching Gradio app.")
    render().launch()
