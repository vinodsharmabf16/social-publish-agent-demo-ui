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
    #logger.info(f"Searching for file: {filename}")
    search_path = os.path.join(directory, filename)
    files = glob.glob(search_path)

    if not files:
        #logger.warning(f"No files found for account: {account_id}")
        return None

    files.sort(key=os.path.getmtime, reverse=True)
    #logger.info(f"Files found: {files}")
    return files[0]

# Load data and return (combined_posts, timestamp)
def load_data():
    response_folder = "response"
    latest_file = get_latest_file(response_folder)
    #logger.info(f"Latest file found: {latest_file}")

    if not latest_file:
        #logger.warning("No latest file found.")
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
        <style>
        .col-image {
                flex: 0 0 20% !important;
                min-width: 150px !important;
                display: flex !important;
                align-items: center !important;
            }
        </style>
        <div class='output-table-row header-row'>
            <div class='col-sno'><strong>S No.</strong></div>
            <div class='col-time'><strong>Suggested Time</strong></div>
            <div class='col-type'><strong>Type</strong></div>
            <div class='col-content'><strong>Content</strong></div>
            <div class='col-image'><strong>Image</strong></div>
        </div>
        """
        for i, post in enumerate(new_data, 1):
            logger.info(f"Processing post {i}")
            content = post.get("content", {})
            post_text = content.get("post", "")
            source = post.get("source", "")
            suggested_time = f"2025-05-14 {10 + i % 12}:00 {('AM' if i % 24 < 12 else 'PM')}"
            image_urls = post.get("image_url", ["https://salonlfc.com/wp-content/uploads/2018/01/image-not-found-scaled-1150x647.png"])
            image_slider_html = ""
            if image_urls:
                for img in image_urls:
                    # img += f"?cb={int(datetime.now().timestamp())}"
                    # img = ""
                    image_slider_html += f"""
        <img src="{img}" width="100" style="margin-right:8px; cursor:pointer;" onclick="openModal(this.src)">
        """
            else:
                image_slider_html = "<img src='https://via.placeholder.com/150' width='100'>"

            html += f"""
                <div class='output-table-row'>
                    <div class='col-sno'>{i}</div>
                    <div class='col-time'>{suggested_time}</div>
                    <div class='col-type'>{source}</div>
                    <div class='col-content'>{post_text}</div>
                    <div class='col-image'>
                        <div class='image-slider'>{image_slider_html}</div>
                    </div>
                </div>
            """

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

        # HTML output table
        table_html_output = gr.HTML(value=initial_html)

        # Button click triggers refresh
        refresh_btn.click(fn=rebuild_table, inputs=[], outputs=[timestamp_display, table_html_output])

        # Add CSS styles
        gr.HTML("""
        <style>
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
            .image-slider {
                display: flex;
                overflow-x: auto;
                gap: 8px;
                max-width: 100%;
                padding-bottom: 4px;
            }
            .image-slider img {
                flex-shrink: 0;
                border-radius: 4px;
            }
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
        </script>

        """)

    return demo

if __name__ == "__main__":
    demo = render()
    demo.launch()
