import gradio as gr

def render():
    gr.Markdown("### Workflow Flowchart")
    gr.Image("./backend/SocialPublishingAgent.png", type="filepath", elem_id="flow-image")
    gr.HTML("""
    <style>
        #flow-image img {
            max-width: 600px !important;
            height: auto !important;
        }
    </style>
    """)
