import gradio as gr
import os
import glob
import json
from dotenv import load_dotenv
from datetime import datetime
from logger import get_logger

logger = get_logger(__name__)

# Utility: Load latest .json file based on ACCOUNT_ID
def get_latest_file(directory):
    load_dotenv(override=True)
    account_id = os.environ.get("ACCOUNT_ID")
    filename = f"{account_id}.json"
    search_path = os.path.join(directory, filename)
    files = glob.glob(search_path)

    if not files:
        return None

    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

# Load data and return (combined_posts, timestamp)
def load_data():
    response_folder = "response"
    latest_file = get_latest_file(response_folder)

    if not latest_file:
        return None, None

    with open(latest_file, "r") as file:
        data = json.load(file)
        logger.info(f"Successfully loaded data from {latest_file}")

    combined_posts = data.get("combined_posts", [])
    return combined_posts, datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Build HTML table layout from data
def rebuild_table():
    new_data, timestamp = load_data()
    logger.info(f"Rebuilding table at {timestamp}")

    timestamp_html = f"<div style='margin-bottom:10px;'>Last updated: {timestamp if timestamp else 'N/A'}</div>"

    html = ""
    if new_data:
        html += """
        <div class='output-table-wrapper'>
        <div class='output-table-row header-row'>
            <div class='col-sno'><strong>S No.</strong></div>
            <div class='col-time'><strong>Suggested Time</strong></div>
            <div class='col-type'><strong>Type</strong></div>
            <div class='col-content'><strong>Content</strong></div>
            <div class='col-image'><strong>Images</strong></div>
        </div>
        """
        for i, post in enumerate(new_data, 1):
            logger.info(f"Processing post {i}")
            content = post.get("content", {})
            post_text = content.get("post", "")
            source = post.get("source", "")
            suggested_time = f"2025-05-14 {10 + i % 12}:00 {('AM' if i % 24 < 12 else 'PM')}"
            image_urls = post.get("image_url", ["https://salonlfc.com/wp-content/uploads/2018/01/image-not-found-scaled-1150x647.png"])
            
            # Create an image display with 4 images in one row
            image_html = "<div class='image-row-container'>"
            
            if image_urls:
                for img in image_urls:
                    image_html += f"""
                    <div class="image-item">
                        <img src="{img}" class="row-image" onclick="openModal(this.src)">
                    </div>
                    """
            else:
                image_html += """
                <div class="image-item">
                    <img src="https://via.placeholder.com/150" class="row-image">
                </div>
                """
            
            image_html += "</div>"

            html += f"""
                <div class='output-table-row'>
                    <div class='col-sno'>{i}</div>
                    <div class='col-time'>{suggested_time}</div>
                    <div class='col-type'>{source}</div>
                    <div class='col-content'>
                        <div class='content-scrollable'>{post_text}</div>
                    </div>
                    <div class='col-image'>{image_html}</div>
                </div>
            """

        html += "</div>"
    else:
        html = "<p>No data found in the response folder.</p>"

    return timestamp_html, html

# Render Gradio UI
def render():
    with gr.Blocks() as demo:
        # Load initial content
        initial_timestamp, initial_html = rebuild_table()

        # Refresh and timestamp row
        with gr.Row():
            refresh_btn = gr.Button("🔄 Refresh Data", elem_id="refresh-btn")
            timestamp_display = gr.HTML(value=initial_timestamp)

        # HTML output table - Full width container
        with gr.Row(elem_id="full-width-container"):
            table_html_output = gr.HTML(value=initial_html)

        # Button click triggers refresh
        refresh_btn.click(fn=rebuild_table, inputs=[], outputs=[timestamp_display, table_html_output])

        # Add CSS styles
        gr.HTML("""
        <style>
            /* Make the container full width */
            #full-width-container {
                width: 100% !important;
                max-width: 100% !important;
                padding: 0 !important;
                margin: 0 !important;
            }
            
            #full-width-container > div {
                width: 100% !important;
                max-width: 100% !important;
            }
            
            .output-table-wrapper {
                width: 100% !important;
                overflow-x: hidden !important;
            }
            
            .output-table-row {
                display: flex !important;
                width: 100% !important;
                margin-bottom: 4px !important;
                gap: 2px !important;
            }
            
            .col-sno {
                flex: 0 0 5% !important;
                min-width: 40px !important;
                display: flex !important;
                align-items: center !important;
            }
            
            .col-time {
                flex: 0 0 7% !important; /* Reduced by half */
                min-width: 90px !important;
                display: flex !important;
                align-items: center !important;
            }
            
            .col-type {
                flex: 0 0 8% !important;
                min-width: 110px !important;
                display: flex !important;
                align-items: center !important;
            }
            
            .col-content {
                flex: 0 0 30% !important; /* Increased content width */
                min-width: 220px !important;
                display: flex !important;
                align-items: flex-start !important; /* Changed to flex-start for better alignment */
                padding: 4px !important;
            }
            
            /* Scrollable content area */
            .content-scrollable {
                max-height: 150px !important; /* Set a max height for the content */
                overflow-y: auto !important; /* Make it scrollable vertically */
                width: 100% !important;
                padding: 4px !important;
            }
            
            .col-image {
                flex: 0 0 50% !important;
                min-width: 300px !important;
                display: flex !important;
                align-items: flex-start !important;
                padding: 8px !important;
            }
            
            .output-table-row > * {
                padding: 4px !important;
                border: 1px solid #eee !important;
                margin: 0 !important;
                box-sizing: border-box !important;
            }
            
            .output-table-row p,
            .output-table-row input {
                margin: 0 !important;
                padding: 0 !important;
                width: 100% !important;
            }
            
            .header-row {
                font-weight: bold !important;
                background-color: #f5f5f5 !important;
            }
            
            #refresh-btn {
                margin-bottom: 15px !important;
                max-width: 200px !important;
            }
            
            /* Image row layout */
            .image-row-container {
                display: flex !important;
                width: 100% !important;
                overflow-x: auto !important;
                gap: 8px !important;
                padding-bottom: 5px !important;
            }
            
            .image-item {
                flex: 0 0 auto !important;
                width: 130px !important;
                height: 130px !important;
                margin-right: 8px !important;
                position: relative !important;
                overflow: hidden !important;
            }
            
            .row-image {
                width: 100% !important;
                height: 100% !important;
                object-fit: cover !important;
                border-radius: 4px !important;
                cursor: pointer !important;
                transition: transform 0.2s !important;
            }
            
            .row-image:hover {
                transform: scale(1.05) !important;
            }
            
            /* Scrollbar styling for content */
            .content-scrollable::-webkit-scrollbar {
                width: 6px !important;
            }
            
            .content-scrollable::-webkit-scrollbar-track {
                background: #f1f1f1 !important;
                border-radius: 10px !important;
            }
            
            .content-scrollable::-webkit-scrollbar-thumb {
                background: #888 !important;
                border-radius: 10px !important;
            }
            
            .content-scrollable::-webkit-scrollbar-thumb:hover {
                background: #555 !important;
            }
            
            /* Modal styles */
            .img-modal {
                display: none;
                position: fixed;
                z-index: 9999;
                padding-top: 60px;
                left: 0; top: 0;
                width: 100%; height: 100%;
                overflow: auto;
                background-color: rgba(0,0,0,0.9);
            }
            
            .modal-content {
                display: block;
                margin: auto;
                max-width: 90%;
                max-height: 80%;
            }
            
            .close-btn {
                position: absolute;
                top: 30px;
                right: 35px;
                color: #fff;
                font-size: 40px;
                font-weight: bold;
                cursor: pointer;
            }
            
            /* Scrollbar for image row */
            .image-row-container::-webkit-scrollbar {
                height: 6px !important;
            }
            
            .image-row-container::-webkit-scrollbar-track {
                background: #f1f1f1 !important;
                border-radius: 10px !important;
            }
            
            .image-row-container::-webkit-scrollbar-thumb {
                background: #888 !important;
                border-radius: 10px !important;
            }
            
            .image-row-container::-webkit-scrollbar-thumb:hover {
                background: #555 !important;
            }
            
            /* Override Gradio's default container constraints */
            .gradio-container {
                max-width: 100% !important;
                width: 100% !important;
                padding: 0 !important;
                margin: 0 auto !important;
            }
            
            .container {
                max-width: 100% !important;
                margin-left: 0 !important;
                margin-right: 0 !important;
                padding-left: 0 !important;
                padding-right: 0 !important;
            }
            
            /* Force full width on Gradio elements */
            .wrap.svelte-10ogue4 {
                max-width: 100% !important;
                padding: 0 10px !important;
            }
        </style>
        
        <!-- Image Modal -->
        <div id="imgModal" class="img-modal" onclick="closeModal()">
            <span class="close-btn">&times;</span>
            <img class="modal-content" id="modalImage">
        </div>
        <script>
        function openModal(src) {
            const modal = document.getElementById("imgModal");
            const modalImg = document.getElementById("modalImage");
            modal.style.display = "block";
            modalImg.src = src;
        }
        function closeModal() {
            document.getElementById("imgModal").style.display = "none";
        }
        
        // Add event listener to ensure full width after Gradio loads
        document.addEventListener("DOMContentLoaded", function() {
            // Force container to full width
            setTimeout(function() {
                const containers = document.querySelectorAll('.gradio-container, .container');
                containers.forEach(container => {
                    container.style.maxWidth = '100%';
                    container.style.width = '100%';
                    container.style.padding = '0';
                    container.style.margin = '0 auto';
                });
            }, 100);
        });
        </script>
        """)

    return demo

if __name__ == "__main__":
    demo = render()
    demo.launch(
        share=False,
        server_port=7860,
        server_name="0.0.0.0",
        inline=False,
    )