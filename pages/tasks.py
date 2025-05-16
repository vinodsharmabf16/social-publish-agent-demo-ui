import requests
import json
import os
import gradio as gr
from gradio_toggle import Toggle
from dotenv import load_dotenv, set_key
from logger import get_logger

logger = get_logger(__name__)

# Global variable to store account ID
ACCOUNT_ID = "default"  # Default account ID

def update_account_id(new_account_id):
    """Update the global account ID"""
    global ACCOUNT_ID
    try:
        logger.info(f"Updating account ID to: {new_account_id}")
        ACCOUNT_ID = new_account_id
        set_key(".env", "ACCOUNT_ID", ACCOUNT_ID)
        logger.info(f"Account ID updated to: {ACCOUNT_ID}")
        return f"✅ Account ID updated to: {ACCOUNT_ID}", gr.update(visible=False)
    except ValueError:
        logger.error("Invalid account ID entered.")
        return "❌ Please enter a valid numeric account ID", gr.update(visible=True)

def collect_prompt_data(prompts_data=None):
    """
    Collect prompt data from the UI components
    If prompts_data is provided, use it; otherwise collect from UI state
    """
    logger.info("Collecting prompt data.")
    if prompts_data:
        # Use provided data (for collecting from UI components)
        return prompts_data
    
    # This is a mock version - you'll replace this with actual UI data collection
    return {
        "account_id": ACCOUNT_ID,
        "number_of_post": 15,
        'small_id': '1148914',
        'long_id': '169030216166956',
        "sources": ["Holiday ideas", "Competitor posts"],
        "prompts": {
            "holiday": ["Suggest content for upcoming holidays", "Another holiday prompt..."],
            "comp": ["Analyze competitor's top posts"]
        }
    }


def publish_from_draft():
    """
    Read the current account's draft file, format the data, and send to API
    """
    global ACCOUNT_ID
    
    # Define the draft file path
    draft_file = f"drafts/{ACCOUNT_ID}.json"
    logger.info(f"Attempting to publish from draft: {draft_file}")
    
    try:
        # Check if draft file exists
        if not os.path.exists(draft_file):
            logger.warning(f"No draft found for Account ID: {ACCOUNT_ID}")
            return f"❌ No draft found for Account ID: {ACCOUNT_ID}"
        
        # Load the draft data
        with open(draft_file, 'r') as f:
            draft_data = json.load(f)
        
        # Extract data from the account section
        account_data = draft_data.get(str(ACCOUNT_ID), {})
        if not account_data:
            logger.warning(f"No data found for Account ID: {ACCOUNT_ID} in draft file")
            return f"❌ No data found for Account ID: {ACCOUNT_ID} in draft file"
        
        # Get prompts and sources from the draft
        prompts = account_data.get("prompts", {})
        sources_dict = account_data.get("sources", {})
        
        # Create list of enabled sources
        sources = [key for key, enabled in sources_dict.items() if enabled]
        
        load_dotenv(override=True)
        total_post = os.environ.get("POSTS_PER_WEEK", "7")
        # Create the API payload
        payload = {
            "account_id": ACCOUNT_ID,
            "total_post": int(total_post), 
              'small_id': '1148914',
    'long_id': '169030216166956',
            "holidays": [
                {"date": "2025-03-09", "holiday": "Diwali"},
                {"date": "2025-03-17", "holiday": "St. Patrick's Day"}
            ],
            "number_of_days": 10,
            "business_info": "We provide expert dental care and cleaning services with cutting-edge equipment and experienced staff.",
            "business_name": "Aspen Dental",
            "business_category":"dental_us",
            "categories": sources,
            "prompt_config": prompts
        }
        logger.info(f"Payload to be sent to API: {payload}")
        # Send to API
        try:
            logger.info(f"Publishing with payload: {json.dumps(payload, indent=2)}")
            response = requests.post("http://localhost:8000/generate-posts", json=payload, timeout=50)
            if response.status_code == 200:
                with open(f"response/{ACCOUNT_ID}.json", "w") as f:
                    json.dump(response.json(), f, indent=4)
                logger.info("API response saved to file.")
                return f"🚀 Published successfully! API response: {response.status_code}"
            else:
                logger.warning(f"API returned status code: {response.status_code}")
                return f"⚠️ API returned status code: {response.status_code}"
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return f"❌ API request failed: {str(e)}"
            
    except Exception as e:
        logger.error(f"Error processing draft: {str(e)}")
        return f"❌ Error processing draft: {str(e)}"


def save_as_draft(*all_values):
    """
    Save the current state of prompts as a JSON file.
    
    Args:
        *all_values: All UI values in sequence:
                    - First 5 values are toggle states
                    - Next 5 values are main prompts
                    - Remaining values are extra prompts (3 per task)
    
    Returns:
        Status message.
    """
    logger.info("Saving current state as draft.")
    task_data = [
        ("Suggest content from business specific post ideas", "Post ideas"),
        ("Suggest content for upcoming holidays", "Holiday ideas"), 
        ("Suggest content from my own top performing posts", "My posts"),
        ("Suggest content from my competitor's top performing posts", "Competitor posts"),
        ("Suggest content from trending topics, relevant to your business", "Trending")
    ]
    
    # Extract toggle states and main prompts
    toggle_states = all_values[:5]
    main_prompts = all_values[5:10]
    extra_prompts_flat = all_values[10:]
    
    # Simplified mapping for task tags
    tag_mapping = {
        "Post ideas": "BUSINESS_IDEAS_POST",
        "Holiday ideas": "HOLIDAY_POST",
        "My posts": "REPURPOSED_POST",
        "Competitor posts": "COMP",
        "Trending": "TRENDING"
    }
    
    prompts = {}
    sources = {}
    
    # Process each task
    for i, ((_, tag), toggle_state, main_prompt) in enumerate(zip(task_data, toggle_states, main_prompts)):
        # Get the simple tag
        simple_tag = tag_mapping.get(tag, tag.lower().replace(" ", "_"))
        
        # Store toggle state
        sources[simple_tag] = toggle_state
        
        if toggle_state:
            # Get extra prompts for this task (3 per task)
            extra_prompts = extra_prompts_flat[i*3:(i+1)*3]
            
            # Combine main and extra prompts, filter out empty ones
            all_task_prompts = [main_prompt] + list(extra_prompts)
            valid_prompts = [p for p in all_task_prompts if p and p.strip()]
            
            if valid_prompts:
                prompts[simple_tag] = valid_prompts
    
    # Create the final data structure using global account ID
    global ACCOUNT_ID
    draft_data = {
        f"{ACCOUNT_ID}": {
            "prompts": prompts,
            "sources": sources
        }
    }
    
    # Save to file
    os.makedirs("drafts", exist_ok=True)
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"drafts/{ACCOUNT_ID}.json"
    
    with open(filename, "w") as f:
        json.dump(draft_data, f, indent=2)
    
    logger.info(f"Draft saved as {filename}")
    return f"✅ Draft saved as {filename}"


# === Placeholder for tag button logic ===
def tag_clicked(tag_label):
    logger.info(f"[Tag clicked]: {tag_label}")
    return


# === Open tools modal ===
def open_tools_modal():
    logger.info("Opening tools modal.")
    return gr.update(visible=True)

# === Close tools modal ===
def close_tools_modal():
    logger.info("Closing tools modal.")
    return gr.update(visible=False)

# === Show/hide the prompt block ===
def toggle_task(enabled):
    logger.info(f"Toggling task block to: {enabled}")
    return gr.update(visible=enabled)


# === Logic for Add Prompt button ===
def add_prompt(count):
    logger.info(f"Add prompt button clicked. Current count: {count}")
    if count < 3:
        return count + 1, *[
            gr.update(visible=(j < count + 1)) for j in range(3)
        ]
    return count, *[gr.update() for _ in range(3)]


# === UI render function ===
def render(on_publish=None):
    gr.HTML("""
    <style>
        #task-header-full {
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-left: 40px;
            padding-right: 40px;
            margin-bottom: 15px;
        }
        
        #task-buttons {
            display: flex;
            gap: 10px;
        }
        
        #task-heading {
            font-size: 18px;
            font-weight: 600;
        }
        
        .task-wrapper {
            max-width: 800px;
            padding-left: 40px;
            padding-right: 20px;
        }
        
        .task-card {
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            background: #fff;
        }
        
        .light-prompt-box {
            position: relative;
        }
        
        .light-prompt-box textarea {
            background-color: #f5f5f5;
            border: none;
            border-radius: 6px;
            padding: 10px;
            font-size: 14px;
            padding-bottom: 30px; /* Make space for the tools button */
        }
        
        .tools-btn {
            position: absolute;
            bottom: 10px;
            left: 10px;
            background: none;
            border: none;
            color: #1a73e8;
            font-size: 14px;
            padding: 2px 5px;
            cursor: pointer;
            z-index: 10;
            opacity: 0.8;
            height: 20px;
        }
        
        .tools-btn:hover {
            opacity: 1;
        }
        
        .add-prompt-btn button {
            background: none;
            border: none;
            color: #1a73e8;
            font-weight: 500;
            font-size: 14px;
            padding-left: 0;
        }
        
        #save-draft-btn {
            background-color: white;
            border: 1px solid #dadce0;
            color: #3c4043;
            font-weight: 500;
        }
        
        #publish-btn {
            background-color: #1a73e8;
            color: white;
            font-weight: 500;
        }
        
        #publish-btn:hover {
            background-color: #1558b0;
        }
        
        #save-draft-btn:hover {
            background-color: #f1f3f4;
        }
        
        /* Settings button and modal */
        #settings-btn {
            background-color: transparent;
            border: none;
            color: #1a73e8;
            cursor: pointer;
            font-size: 24px;
        }
        
        #settings-modal {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.2);
            padding: 24px;
            z-index: 1000;
            width: 400px;
        }
        
        /* Tool selection modal - positioned on the right */
        #tools-modal {
            position: fixed;
            top: 0;
            right: 0;
            bottom: 0;
            width: 520px;
            background-color: white;
            box-shadow: -4px 0 12px rgba(0,0,0,0.1);
            padding: 0;
            z-index: 1000;
            overflow-y: auto;
        }
        
        #modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0,0,0,0.5);
            z-index: 999;
        }
        
        .settings-header, .tools-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0;
            border-bottom: 1px solid #eee;
            padding: 16px 20px;
        }
        
        .tools-title-row {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .back-button {
            font-size: 20px;
            cursor: pointer;
            color: #5f6368;
        }
        
        .tools-header h3 {
            font-size: 18px;
            font-weight: 500;
            margin: 0;
        }
        
        .settings-close, .tools-close {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #5f6368;
        }
        
        .settings-content {
            margin-bottom: 20px;
        }
        
        /* Tools filter and search */
        .tools-filter-row {
            padding: 10px 20px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .tools-filter {
            color: #3c4043;
            font-size: 14px;
        }
        
        .tool-category {
            color: #1a73e8;
            font-weight: 500;
            cursor: pointer;
        }
        
        .dropdown-arrow {
            font-size: 10px;
            margin-left: 4px;
            color: #1a73e8;
        }
        
        .tools-search {
            width: 40%;
            background-color: #f1f3f4;
            border-radius: 4px;
            padding: 8px 12px;
            border: none;
        }
        
        /* Section header styles */
        .tools-section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px 8px;
            border-bottom: 1px solid #eee;
        }
        
        .tools-section-header h4 {
            margin: 0;
            font-size: 14px;
            font-weight: 500;
            color: #3c4043;
        }
        
        /* Tool list item styles */
        .tools-list {
            padding: 0;
        }
        
        .tool-item {
            display: flex;
            align-items: flex-start;
            padding: 16px 20px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
        }
        
        .tool-item:hover {
            background-color: #f8f9fa;
        }
        
        .tool-icon {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 16px;
            background-color: #f1f3f4;
            flex-shrink: 0;
        }
        
        .tool-icon img {
            width: 24px;
            height: 24px;
        }
        
        .tool-icon.instagram {
            background-color: #ffebf5;
        }
        
        .tool-icon.instagram img {
            color: #e1306c;
        }
        
        .tool-icon.twitter {
            background-color: #e8f5fe;
        }
        
        .tool-icon.twitter img {
            color: #1DA1F2;
        }
        
        .tool-icon.facebook {
            background-color: #e9f3ff;
        }
        
        .tool-icon.facebook img {
            color: #4267B2;
        }
        
        .tool-icon.google {
            background-color: #f5f5f5;
        }
        
        .tool-content {
            flex-grow: 1;
        }
        
        .tool-name {
            font-weight: 500;
            margin-bottom: 4px;
            color: #3c4043;
        }
        
        .tool-description {
            font-size: 14px;
            color: #5f6368;
        }
        
        /* Status message styling */
        #status-message {
            margin-top: 10px;
            padding: 8px;
            border-radius: 4px;
            background-color: #e8f0fe;
            color: #1a73e8;
        }
        
        /* Hide footer */
        footer, .svelte-13f7f5i, .svelte-1ipelgc {
            display: none !important;
        }
        
        /* Hide settings panel button (gear icon) */
        #component-0 .absolute.top-4.right-4 {
            display: none !important;
        }
    
    </style>
    """)

    # Lists to collect all UI components for inputs
    all_toggles = []
    all_main_prompts = []
    all_extra_prompts = []
    
    # Status message for save/publish operations
    status_message = gr.Markdown("", elem_id="status-message")

    # Settings modal (initially hidden)
    with gr.Group(visible=False, elem_id="settings-modal") as settings_modal:
        with gr.Column():
            with gr.Row(elem_classes=["settings-header"]):
                gr.Markdown("### Settings")
                close_settings_btn = gr.Button("×", elem_classes=["settings-close"])
            
            account_id_input = gr.Textbox(
                label="Account ID", 
                value=str(ACCOUNT_ID),
                info="Enter your account ID"
            )
            settings_status = gr.Markdown("")
            save_settings_btn = gr.Button("Save Settings", variant="primary")
            
    # Tools modal (initially hidden) - Now showing social tools selection
    with gr.Group(visible=False, elem_id="tools-modal") as tools_modal:
        with gr.Column():
            with gr.Row(elem_classes=["tools-header"]):
                gr.HTML("""
                <div class="tools-title-row">
                    
                    <h3>Add tool</h3>
                </div>
                """)
                close_tools_btn = gr.Button("×", elem_classes=["tools-close"])
            
            # Filter and search section
            with gr.Row(elem_classes=["tools-filter-row"]):
                gr.HTML("""
                <div class="tools-filter">
                    <span>Showing - </span>
                    <span class="tool-category">Social tools</span>
                    <span class="dropdown-arrow">▼</span>
                </div>
                """)
                search_input = gr.Textbox(
                    placeholder="Search",
                    show_label=False,
                    elem_classes=["tools-search"]
                )
            
            # Connected tools section
            gr.HTML("""
            <div class="tools-section-header">
                <h4>Connected tools</h4>
                <span class="dropdown-arrow">▼</span>
            </div>
            """)
            
            # Tool list items
            with gr.Column(elem_classes=["tools-list"]):
                # Instagram tool
                with gr.Row(elem_classes=["tool-item"]):
                    gr.HTML("""
                    <div class="tool-icon instagram">
                        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJsdWNpZGUgbHVjaWRlLWluc3RhZ3JhbSI+PHJlY3Qgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIiB4PSIyIiB5PSIyIiByeD0iNSIvPjxwYXRoIGQ9Ik0xNiAxMS4zN0E0IDQgMCAxIDEgMTIuNjMgOCA0IDQgMCAwIDEgMTYgMTEuMzd6Ii8+PGxpbmUgeDE9IjE3LjUiIHgyPSIxNy41MSIgeTE9IjYuNSIgeTI9IjYuNSIvPjwvc3ZnPg==" alt="Instagram" />
                    </div>
                    <div class="tool-content">
                        <div class="tool-name">Get best time to post • Instagram</div>
                        <div class="tool-description">This solution analyzes engagement patterns to find the best times to share your content.</div>
                    </div>
                    """)
                
                # Twitter tool
                with gr.Row(elem_classes=["tool-item"]):
                    gr.HTML("""
                    <div class="tool-icon twitter">
                        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJsdWNpZGUgbHVjaWRlLXR3aXR0ZXIiPjxwYXRoIGQ9Ik0yMiA0cy0uNyAyLjEtMiAzLjRjMS42IDEwLTkuNCAxNy4zLTE4IDExLjYgMi4yLjEgNC40LS42IDYtMi0zLjQtLjEtNS40LTIuNS02LTQuOCAxLjEuMiAyLjIgMCAzLS4zQzIgMTEuNiAwIDkuNCAwIDUuOGMuOS41IDEuOC43IDIuOC43QzEgNC44LS4yIDIuMSAxIDAgNCA0LjMgOCA2LjUgMTMgNi43Yy0uNy0zIDEuNi02IDQuNS02IDEuNCAwIDIuNi42IDMuNSAxLjVDMjIuMiAyIDIzIDEuNSAyNCAxYy0uMiAxLjEtMSAyLTEuNSAyLjVjMSAuMSAxLjgtLjMgMi41LS41eiIvPjwvc3ZnPg==" alt="Twitter" />
                    </div>
                    <div class="tool-content">
                        <div class="tool-name">Get twitter trends • Twitter</div>
                        <div class="tool-description"></div>
                    </div>
                    """)
                
                # Facebook post tool
                with gr.Row(elem_classes=["tool-item"]):
                    gr.HTML("""
                    <div class="tool-icon facebook">
                        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJsdWNpZGUgbHVjaWRlLWZhY2Vib29rIj48cGF0aCBkPSJNMTggMkgxNWEzIDMgMCAwIDAtMyAzdjNIMXYyaDExdjEwaDJ2LTEwaDRsMS0yaC01VjVhMSAxIDAgMCAxIDEtMWgzeiIvPjwvc3ZnPg==" alt="Facebook" />
                    </div>
                    <div class="tool-content">
                        <div class="tool-name">Create post • Facebook</div>
                        <div class="tool-description">Creates a new post on a page on Facebook</div>
                    </div>
                    """)
                
                # Facebook insights tool
                with gr.Row(elem_classes=["tool-item"]):
                    gr.HTML("""
                    <div class="tool-icon facebook">
                        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJsdWNpZGUgbHVjaWRlLWZhY2Vib29rIj48cGF0aCBkPSJNMTggMkgxNWEzIDMgMCAwIDAtMyAzdjNIMXYyaDExdjEwaDJ2LTEwaDRsMS0yaC01VjVhMSAxIDAgMCAxIDEtMWgzeiIvPjwvc3ZnPg==" alt="Facebook" />
                    </div>
                    <div class="tool-content">
                        <div class="tool-name">Get page insights • Facebook</div>
                        <div class="tool-description">Gets insights for a page on Facebook</div>
                    </div>
                    """)
                
                # Facebook message tool
                with gr.Row(elem_classes=["tool-item"]):
                    gr.HTML("""
                    <div class="tool-icon facebook">
                        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJsdWNpZGUgbHVjaWRlLWZhY2Vib29rIj48cGF0aCBkPSJNMTggMkgxNWEzIDMgMCAwIDAtMyAzdjNIMXYyaDExdjEwaDJ2LTEwaDRsMS0yaC01VjVhMSAxIDAgMCAxIDEtMWgzeiIvPjwvc3ZnPg==" alt="Facebook" />
                    </div>
                    <div class="tool-content">
                        <div class="tool-name">Send message • Facebook</div>
                        <div class="tool-description">Sends a message to a user from a Facebook page</div>
                    </div>
                    """)
                
                # Google Search tool
                with gr.Row(elem_classes=["tool-item"]):
                    gr.HTML("""
                    <div class="tool-icon google">
                        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJsdWNpZGUgbHVjaWRlLWdvb2dsZSI+PHBhdGggZD0iTTEyIDI0QzYuNDc3MyAyNCAxLjg1NzUgMjAgMC45NDAxNCAxNC4zMDY4QzAuMDMwMDMgOC42MjUyNyAzLjk2OSAzLjM5NDY4IDkuNTUyMDEgMS42MjQzOUMxMy42MzE3IDAuMzg1NDIzIDE4LjA3MSAyLjA3MDE0IDIwLjQ4MiA1LjY0MzEyIi8+PHBhdGggZD0iTTEyIDAgQzY1LjM4IDAuODI1NSA5LjExIDMuMzM4MyA4LjUzIDYuOTA3NyBDOC4yMSA4LjYyMzcgOC42NyAxMC4zMzk3IDkuNjggMTEuNjk2NyBDMTAuNjkxIDEzLjA1MzcgMTIuMzcxIDEzLjcwMzcgMTQgMTMuMzA4NyBDMTUuNjI5MSAxMi45MTM3IDE2Ljk1MDEgMTEuNjM0NyAxNy4zODAxIDEwLjAxMjcgQzE3LjgxMDEgOC4zOTA3IDE3LjQ2MDEgNi42NzA3IDE2LjM4MTEgNS4zMTE3Ii8+PHBhdGggZD0iTTIwIDkuNUExMC41IDEwLjUgMCAxIDEgOS41IDIwSDEyVjE1LjA5QzEyLjAxNTggMTQuNjQ5NSAxMi4xMjg0IDE0LjIxNjggMTIuMzMgMTMuODJDMTMuMzQ3IDE3LjExMTYgMTYuODMzOCAxOC45MzM5IDIwIDIwIi8+PC9zdmc+" alt="Google" />
                    </div>
                    <div class="tool-content">
                        <div class="tool-name">Google Search • Google</div>
                        <div class="tool-description">Get Google Search results using a search query</div>
                    </div>
                    """)
                

    # === Top Heading + Buttons in Full Width ===
    with gr.Row(elem_id="task-header-full"):
        gr.Markdown("### Configure the tasks the agent will perform", elem_id="task-heading")
        with gr.Row(elem_id="task-buttons"):
            settings_btn = gr.Button("⚙️", elem_id="settings-btn")
            publish_btn = gr.Button("Publish", elem_id="publish-btn", variant="primary")
            save_btn = gr.Button("Save as draft", elem_id="save-draft-btn")
            logger.info(f"Task settings updated")
    # Toggle settings modal visibility
    settings_btn.click(
        fn=lambda: gr.update(visible=True),
        outputs=[settings_modal]
    )
    
    # Close settings modal
    close_settings_btn.click(
        fn=lambda: gr.update(visible=False),
        outputs=[settings_modal]
    )
    
    # Close tools modal
    close_tools_btn.click(
        fn=close_tools_modal,
        outputs=[tools_modal]
    )
    
    # Save settings
    save_settings_btn.click(
        fn=update_account_id,
        inputs=[account_id_input],
        outputs=[settings_status, settings_modal]
    )

    # === Main task section
    with gr.Column(elem_classes=["task-wrapper"]):
        task_data = [
            ("Analyze content based on Business specific post ideas", "Generate post ideas based on the business context.", "Post ideas"),
            ("Analyze content for Upcoming holidays","Generate post for upcoming holidays.", "Holiday ideas"),
            ("Suggest content based on top performing post","Generate new posts based on your top performing posts.", "My posts"),
            ("Content based on your competitors' posts","Generate new posts based on your top performing posts.", "Competitor posts"),
            ("Analyze content based on the trends","Create posts based on the latest trends", "Trending")
        ]

        for i, (heading, title, tag) in enumerate(task_data, start=1):
            with gr.Column(elem_classes=["task-card"]):
                with gr.Row():
                    with gr.Column(scale=11):
                        gr.Markdown(f"**{i}. {heading}**")
                    with gr.Column(scale=1, min_width=80):
                        toggle = Toggle(value=True, color="blue", label="")
                        all_toggles.append(toggle)

                with gr.Column(visible=True) as content_block:
                    with gr.Row():
                        # Custom HTML for the main prompt with tools button
                        with gr.Column(scale=8):
                            with gr.Group(elem_classes=["light-prompt-box"]):
                                main_prompt = gr.Textbox(
                                    value=f" {title}",
                                    interactive=True,
                                    show_label=False,
                                    lines=2,
                                    elem_id=f"main-prompt-{i}"
                                )
                                tools_btn = gr.Button("🔧 Tools", elem_classes=["tools-btn"])
                                tools_btn.click(
                                    fn=open_tools_modal,
                                    outputs=[tools_modal]
                                )
                            all_main_prompts.append(main_prompt)
                        
                        tag_btn = gr.Button(f"⚙️ {tag}", size="sm", scale=2)
                        tag_btn.click(fn=lambda t=tag: tag_clicked(t), outputs=[])

                    # For extra prompts
                    prompt_count = gr.State(0)
                    extra_prompts_containers = []
                    extra_prompts = []
                    
                    # for j in range(3):
                    #     with gr.Group(visible=False, elem_classes=["light-prompt-box"]) as extra_container:
                    #         extra_prompt = gr.Textbox(
                    #             placeholder="New prompt...",
                    #             interactive=True,
                    #             show_label=False,
                    #             lines=2
                    #         )
                    #         extra_tools_btn = gr.Button("🔧 Tools", elem_classes=["tools-btn"])
                    #         extra_tools_btn.click(
                    #             fn=open_tools_modal,
                    #             outputs=[tools_modal]
                    #         )
                    #         extra_prompts.append(extra_prompt)
                    #         extra_prompts_containers.append(extra_container)
                    
                    # all_extra_prompts.extend(extra_prompts)
                    
                    # add_btn = gr.Button("➕ Add prompt", size="sm", elem_classes=["add-prompt-btn"])
                    # add_btn.click(
                    #     add_prompt,
                    #     inputs=[prompt_count],
                    #     outputs=[prompt_count] + extra_prompts_containers
                    # )

                toggle.change(
                    fn=toggle_task,
                    inputs=[toggle],
                    outputs=[content_block]
                )
    
    # Handle Save as Draft button - pass all input components directly
    all_inputs = all_toggles + all_main_prompts + all_extra_prompts
    save_btn.click(
        fn=save_as_draft,
        inputs=all_inputs,
        outputs=[status_message]
    )
    
    # Handle Publish button - now using the publish_from_draft function
    publish_btn.click(
        fn=publish_from_draft,
        outputs=[status_message]
    )
    
    return status_message