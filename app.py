import gradio as gr
from pages import outcomes, tasks, output, flow
from startup import render_startup

def render():
    with gr.Blocks(title="Social Publishing Agent", theme=gr.themes.Default(primary_hue="blue")) as demo:
        gr.Markdown("## Social publishing agent", elem_id="main-header")

        # === App State ===
        show_main_app = gr.State(False)

        # === Startup Screen ===
        with gr.Column(visible=True) as startup_screen:
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
                outcomes.render()
            with gr.Tab("Tasks"):
                # Trigger for showing Output page
                tasks.render(on_publish=lambda: gr.update(visible=True))  # Use gr.update to show Output tab
            with gr.Tab("Output", visible=True) as output_tab:  # Start with Output tab hidden
                output.render()
            with gr.Tab("Flow"):
                flow.render()


        continue_btn.click(
            fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
            outputs=[startup_screen, main_tabs]
        )

    return demo

if __name__ == "__main__":
    render().launch()
