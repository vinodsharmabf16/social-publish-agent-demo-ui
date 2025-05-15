import requests
import json
import os
import gradio as gr
from gradio_toggle import Toggle
from dotenv import load_dotenv, set_key

# Global variable to store account ID
ACCOUNT_ID = "default"  # Default account ID

def update_account_id(new_account_id):
    """Update the global account ID"""
    global ACCOUNT_ID
    try:
        ACCOUNT_ID = new_account_id
        set_key(".env", "ACCOUNT_ID", ACCOUNT_ID)
        return f"✅ Account ID updated to: {ACCOUNT_ID}", gr.update(visible=False)
    except ValueError:
        return "❌ Please enter a valid numeric account ID", gr.update(visible=True)

def collect_prompt_data(prompts_data=None):
    """
    Collect prompt data from the UI components
    If prompts_data is provided, use it; otherwise collect from UI state
    """
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
    
    try:
        # Check if draft file exists
        if not os.path.exists(draft_file):
            return f"❌ No draft found for Account ID: {ACCOUNT_ID}"
        
        # Load the draft data
        with open(draft_file, 'r') as f:
            draft_data = json.load(f)
        
        # Extract data from the account section
        account_data = draft_data.get(str(ACCOUNT_ID), {})
        if not account_data:
            return f"❌ No data found for Account ID: {ACCOUNT_ID} in draft file"
        
        # Get prompts and sources from the draft
        prompts = account_data.get("prompts", {})
        sources_dict = account_data.get("sources", {})
        
        # Create list of enabled sources
        sources = [key for key, enabled in sources_dict.items() if enabled]
        
        # Create the API payload
        payload = {
            "account_id": ACCOUNT_ID,
            "total_post": 5,  # Default value
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
        print("📦 Payload to be sent to API:", payload)
        # Send to API
        try:
            print(f"🚀 Publishing with payload -----========: {json.dumps(payload, indent=2)}")
            response = requests.post("http://localhost:8000/generate-posts", json=payload, timeout=70)
            if response.status_code == 200:
                with open(f"response/{ACCOUNT_ID}.json", "w") as f:
                    json.dump(response.json(), f, indent=4)
                print("📦 API response saved to file.")
                return f"🚀 Published successfully! API response: {response.status_code}"
            else:
                return f"⚠️ API returned status code: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return f"❌ API request failed: {str(e)}"
            
    except Exception as e:
        return f"❌ Error processing draft: {str(e)}"


# def publish():
#     data = collect_prompt_data()
#     res = requests.post("http://localhost:8000/publish", json=data)
#     return f"🚀 Published: {res.status_code}"


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
    
    return f"✅ Draft saved as {filename}"


# === Placeholder for tag button logic ===
def tag_clicked(tag_label):
    print(f"[Tag clicked]: {tag_label}")
    return


# === Show/hide the prompt block ===
def toggle_task(enabled):
    return gr.update(visible=enabled)


# === Logic for Add Prompt button ===
def add_prompt(count):
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
        
        .light-prompt-box textarea {
            background-color: #f5f5f5;
            border: none;
            border-radius: 6px;
            padding: 10px;
            font-size: 14px;
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
        
        #modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0,0,0,0.5);
            z-index: 999;
        }
        
        .settings-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        
        .settings-header h3 {
            margin: 0;
        }
        
        .settings-close {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
        }
        
        .settings-content {
            margin-bottom: 20px;
        }
        
        .settings-footer {
            display: flex;
            justify-content: flex-end;
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
    with gr.Group(visible=False) as settings_modal:
        gr.Markdown("### Settings")
        account_id_input = gr.Textbox(
            label="Account ID", 
            value=str(ACCOUNT_ID),
            info="Enter your account ID"
        )
        settings_status = gr.Markdown("")
        save_settings_btn = gr.Button("Save Settings", variant="primary")
        save_settings_btn.click(
            fn=update_account_id,
            inputs=[account_id_input],
            outputs=[settings_status, settings_modal]
        )

    # === Top Heading + Buttons in Full Width ===
    with gr.Row(elem_id="task-header-full"):
        gr.Markdown("### Configure the tasks the agent will perform", elem_id="task-heading")
        with gr.Row(elem_id="task-buttons"):
            settings_btn = gr.Button("⚙️", elem_id="settings-btn")
            publish_btn = gr.Button("Publish", elem_id="publish-btn", variant="primary")
            save_btn = gr.Button("Save as draft", elem_id="save-draft-btn")

    # Toggle settings modal visibility
    settings_btn.click(
        fn=lambda: gr.update(visible=True),
        outputs=[settings_modal]
    )

    # === Main task section
    with gr.Column(elem_classes=["task-wrapper"]):
        task_data = [
            ("Suggest content from business specific post ideas", "Post ideas"),
            ("Suggest content for upcoming holidays", "Holiday ideas"),
            ("Suggest content from my own top performing posts", "My posts"),
            ("Suggest content from my competitor's top performing posts", "Competitor posts"),
            ("Suggest content from trending topics, relevant to your business", "Trending")
        ]

        for i, (title, tag) in enumerate(task_data, start=1):
            with gr.Column(elem_classes=["task-card"]):
                with gr.Row():
                    with gr.Column(scale=11):
                        gr.Markdown(f"**{i}. {title}**")
                    with gr.Column(scale=1, min_width=80):
                        toggle = Toggle(value=True, color="blue", label="")
                        all_toggles.append(toggle)

                with gr.Column(visible=True) as content_block:
                    with gr.Row():
                        main_prompt = gr.Textbox(
                            value=f"Identify {title.lower()} using",
                            interactive=True,
                            show_label=False,
                            lines=1,
                            elem_classes=["light-prompt-box"],
                            scale=8
                        )
                        all_main_prompts.append(main_prompt)
                        
                        tag_btn = gr.Button(f"⚙️ {tag}", size="sm", scale=2)
                        tag_btn.click(fn=lambda t=tag: tag_clicked(t), outputs=[])

                    # For extra prompts
                    prompt_count = gr.State(0)
                    extra_prompts = [
                        gr.Textbox(
                            placeholder="New prompt...",
                            visible=False,
                            interactive=True,
                            show_label=False,
                            elem_classes=["light-prompt-box"]
                        ) for _ in range(3)
                    ]
                    all_extra_prompts.extend(extra_prompts)
                    
                    add_btn = gr.Button("➕ Add prompt", size="sm", elem_classes=["add-prompt-btn"])
                    add_btn.click(
                        add_prompt,
                        inputs=[prompt_count],
                        outputs=[prompt_count] + extra_prompts
                    )

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