import gradio as gr

def render():
    dummy_img_url = "https://images.pexels.com/photos/6627574/pexels-photo-6627574.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2"

    # Sample data
    output_data = [
        (1, "2025-05-15 10:00 AM", "Idea", "Here's your first generated post."),
        (2, "2025-05-15 12:00 PM", "Holiday", "Another great piece of content."),
        (3, "2025-05-15 02:00 PM", "Competitor", "Here's a third idea, fresh af."),
        (4, "2025-05-15 04:00 PM", "Trend", "Let's keep it going with this one."),
        (5, "2025-05-15 06:00 PM", "My Posts", "Last one! Time to publish this.")
    ]

    # Create the layout
    with gr.Column() as main_column:
        # Custom CSS in a HTML component
        gr.HTML("""
        <style>
            /* Target Gradio's row containers */
            .output-table-row {
                display: flex !important;
                width: 100% !important;
                margin-bottom: 4px !important;
                gap: 2px !important;
            }
            
            /* Column width styles */
            .col-sno {
                flex: 0 0 5% !important;
                min-width: 40px !important;
                display: flex !important;
                align-items: center !important;
            }
            
            .col-time {
                flex: 0 0 20% !important;
                min-width: 150px !important;
                display: flex !important;
                align-items: center !important;
            }
            
            .col-type {
                flex: 0 0 15% !important;
                min-width: 100px !important;
                display: flex !important;
                align-items: center !important;
            }
            
            .col-content {
                flex: 0 0 30% !important;
                min-width: 250px !important;
                display: flex !important;
                align-items: center !important;
            }
            
            .col-image {
                flex: 0 0 20% !important;
                min-width: 150px !important;
                display: flex !important;
                align-items: center !important;
            }
            
            /* Add minimal padding and borders to make it look like a table */
            .output-table-row > * {
                padding: 4px !important;
                border: 1px solid #eee !important;
                margin: 0 !important;
                box-sizing: border-box !important;
            }
            
            /* Remove default Gradio component margins and ensure consistent width */
            .output-table-row > * > div {
                margin: 0 !important;
                width: 100% !important;
            }
            
            /* Force consistent sizing for all cells */
            .output-table-row p,
            .output-table-row textarea,
            .output-table-row input {
                margin: 0 !important;
                padding: 0 !important;
                width: 100% !important;
            }
            
            /* Header row styling */
            .header-row {
                font-weight: bold !important;
                background-color: #f5f5f5 !important;
            }
            
            /* Ensure text inputs and markdown have same alignment */
            .output-table-row .gradio-markdown,
            .output-table-row .gradio-textbox {
                width: 100% !important;
            }
            
            /* Fix for header text alignment */
            .header-row .gradio-markdown {
                display: flex !important;
                align-items: center !important;
                height: 100% !important;
            }
        </style>
        """)
        
        # Create a container for our table
        with gr.Column():
            # Header row with customized class
            with gr.Row(elem_classes=["output-table-row", "header-row"]):
                gr.Markdown("**S No.**", elem_classes="col-sno")
                gr.Markdown("**Suggested Time**", elem_classes="col-time")
                gr.Markdown("**Type**", elem_classes="col-type")
                gr.Markdown("**Content**", elem_classes="col-content")
                gr.Markdown("**Image**", elem_classes="col-image")

            # Data rows with customized classes
            for sno, suggested_time, type_label, content in output_data:
                with gr.Row(elem_classes="output-table-row"):
                    gr.Textbox(value=str(sno), interactive=False, show_label=False, 
                              elem_classes="col-sno")
                    gr.Textbox(value=suggested_time, interactive=False, show_label=False,
                              elem_classes="col-time")
                    gr.Textbox(value=type_label, interactive=False, show_label=False,
                              elem_classes="col-type")
                    gr.Textbox(value=content, lines=2, interactive=False, show_label=False,
                              elem_classes="col-content")
                    gr.Image(value=dummy_img_url, show_label=False, interactive=False,
                            elem_classes="col-image")

    return main_column

if __name__ == "__main__":
    with gr.Blocks() as demo:
        render()
    demo.launch()