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

# Global UI component references
tools_modal = None
holiday_detail_view = None
business_posts_detail_view = None
competitor_posts_detail_view = None
business_ideas_detail_view = None
trending_topics_detail_view = None

def save_business_posts_config(get_all, get_facebook, get_twitter, get_instagram, num_posts, metric):
    """
    Save business posts tool configuration with individual entries for each selected platform.
    Unselected platforms are removed from the configuration.
    """
    global ACCOUNT_ID
    logger.info(f"Saving business posts tool configuration")
    
    draft_file = f"drafts/{ACCOUNT_ID}.json"
    
    try:
        # Create drafts directory if it doesn't exist
        os.makedirs("drafts", exist_ok=True)
        
        # Load existing data if file exists
        if os.path.exists(draft_file):
            with open(draft_file, 'r') as f:
                draft_data = json.load(f)
        else:
            draft_data = {
                str(ACCOUNT_ID): {
                    "prompts": {},
                    "sources": {},
                    "tools": {}
                }
            }
        
        # Ensure the account section exists
        if str(ACCOUNT_ID) not in draft_data:
            draft_data[str(ACCOUNT_ID)] = {
                "prompts": {},
                "sources": {},
                "tools": {}
            }
        
        # Ensure tools section exists
        if "tools" not in draft_data[str(ACCOUNT_ID)]:
            draft_data[str(ACCOUNT_ID)]["tools"] = {}
        
        # Initialize tool type if needed
        if "REPURPOSED_POST" not in draft_data[str(ACCOUNT_ID)]["tools"]:
            draft_data[str(ACCOUNT_ID)]["tools"]["REPURPOSED_POST"] = []
        
        # Clear existing configurations - this removes all previous configurations
        draft_data[str(ACCOUNT_ID)]["tools"]["REPURPOSED_POST"] = []
        
        # Add new configurations based on selected platforms
        if get_all:
            # If "all" is selected, add just one config for all
            draft_data[str(ACCOUNT_ID)]["tools"]["REPURPOSED_POST"].append({
                "name": "Get Top performing posts - all",
                "config": {
                    "num_posts": int(num_posts),
                    "evaluation_metric": metric
                }
            })
        else:
            # Add individual configurations for each selected platform
            if get_facebook:
                draft_data[str(ACCOUNT_ID)]["tools"]["REPURPOSED_POST"].append({
                    "name": "Get Top performing posts - facebook",
                    "config": {
                        "num_posts": int(num_posts),
                        "evaluation_metric": metric
                    }
                })
            
            if get_twitter:
                draft_data[str(ACCOUNT_ID)]["tools"]["REPURPOSED_POST"].append({
                    "name": "Get Top performing posts - twitter",
                    "config": {
                        "num_posts": int(num_posts),
                        "evaluation_metric": metric
                    }
                })
            
            if get_instagram:
                draft_data[str(ACCOUNT_ID)]["tools"]["REPURPOSED_POST"].append({
                    "name": "Get Top performing posts - instagram",
                    "config": {
                        "num_posts": int(num_posts),
                        "evaluation_metric": metric
                    }
                })
        
        # Save updated data
        with open(draft_file, 'w') as f:
            json.dump(draft_data, f, indent=2)
        
        logger.info(f"Business posts tool configuration saved")
        return f"✅ Business posts tool configuration saved"
    
    except Exception as e:
        logger.error(f"Error saving business posts tool configuration: {str(e)}")
        return f"❌ Error saving business posts tool configuration: {str(e)}"

def save_competitor_posts_config(get_all, get_facebook, get_twitter, get_instagram, num_posts, metric):
    """
    Save competitor posts tool configuration with individual entries for each selected platform.
    Unselected platforms are removed from the configuration.
    """
    global ACCOUNT_ID
    logger.info(f"Saving competitor posts tool configuration")
    
    draft_file = f"drafts/{ACCOUNT_ID}.json"
    
    try:
        # Create drafts directory if it doesn't exist
        os.makedirs("drafts", exist_ok=True)
        
        # Load existing data if file exists
        if os.path.exists(draft_file):
            with open(draft_file, 'r') as f:
                draft_data = json.load(f)
        else:
            draft_data = {
                str(ACCOUNT_ID): {
                    "prompts": {},
                    "sources": {},
                    "tools": {}
                }
            }
        
        # Ensure the account section exists
        if str(ACCOUNT_ID) not in draft_data:
            draft_data[str(ACCOUNT_ID)] = {
                "prompts": {},
                "sources": {},
                "tools": {}
            }
        
        # Ensure tools section exists
        if "tools" not in draft_data[str(ACCOUNT_ID)]:
            draft_data[str(ACCOUNT_ID)]["tools"] = {}
        
        # Initialize tool type if needed
        if "COMP" not in draft_data[str(ACCOUNT_ID)]["tools"]:
            draft_data[str(ACCOUNT_ID)]["tools"]["COMP"] = []
        
        # Clear existing configurations - this removes all previous configurations
        draft_data[str(ACCOUNT_ID)]["tools"]["COMP"] = []
        
        # Add new configurations based on selected platforms
        if get_all:
            # If "all" is selected, add just one config for all
            draft_data[str(ACCOUNT_ID)]["tools"]["COMP"].append({
                "name": "Get Top performing posts - all",
                "config": {
                    "num_posts": int(num_posts),
                    "evaluation_metric": metric
                }
            })
        else:
            # Add individual configurations for each selected platform
            if get_facebook:
                draft_data[str(ACCOUNT_ID)]["tools"]["COMP"].append({
                    "name": "Get Top performing posts - facebook",
                    "config": {
                        "num_posts": int(num_posts),
                        "evaluation_metric": metric
                    }
                })
            
            if get_twitter:
                draft_data[str(ACCOUNT_ID)]["tools"]["COMP"].append({
                    "name": "Get Top performing posts - twitter",
                    "config": {
                        "num_posts": int(num_posts),
                        "evaluation_metric": metric
                    }
                })
            
            if get_instagram:
                draft_data[str(ACCOUNT_ID)]["tools"]["COMP"].append({
                    "name": "Get Top performing posts - instagram",
                    "config": {
                        "num_posts": int(num_posts),
                        "evaluation_metric": metric
                    }
                })
        
        # Save updated data
        with open(draft_file, 'w') as f:
            json.dump(draft_data, f, indent=2)
        
        logger.info(f"Competitor posts tool configuration saved")
        return f"✅ Competitor posts tool configuration saved"
    
    except Exception as e:
        logger.error(f"Error saving competitor posts tool configuration: {str(e)}")
        return f"❌ Error saving competitor posts tool configuration: {str(e)}"

def save_tool_config(tool_type, config_data):
    """
    Save tool configuration to the account's draft file
    
    Args:
        tool_type: The type of tool (e.g., HOLIDAY_POST, REPURPOSED_POST)
        config_data: Dictionary containing the tool's configuration
    
    Returns:
        Status message
    """
    global ACCOUNT_ID
    logger.info(f"Saving tool configuration for {tool_type}")
    
    draft_file = f"drafts/{ACCOUNT_ID}.json"
    
    try:
        # Create drafts directory if it doesn't exist
        os.makedirs("drafts", exist_ok=True)
        
        # Load existing data if file exists
        if os.path.exists(draft_file):
            with open(draft_file, 'r') as f:
                draft_data = json.load(f)
        else:
            draft_data = {
                str(ACCOUNT_ID): {
                    "prompts": {},
                    "sources": {},
                    "tools": {}
                }
            }
        
        # Ensure the account section exists
        if str(ACCOUNT_ID) not in draft_data:
            draft_data[str(ACCOUNT_ID)] = {
                "prompts": {},
                "sources": {},
                "tools": {}
            }
        
        # Ensure tools section exists
        if "tools" not in draft_data[str(ACCOUNT_ID)]:
            draft_data[str(ACCOUNT_ID)]["tools"] = {}
        
        # Add/update the tool configuration
        if tool_type not in draft_data[str(ACCOUNT_ID)]["tools"]:
            draft_data[str(ACCOUNT_ID)]["tools"][tool_type] = []
        
        # Update or add the tool config
        tool_exists = False
        for i, tool in enumerate(draft_data[str(ACCOUNT_ID)]["tools"][tool_type]):
            if tool["name"] == config_data["name"]:
                draft_data[str(ACCOUNT_ID)]["tools"][tool_type][i] = config_data
                tool_exists = True
                break
        
        if not tool_exists:
            draft_data[str(ACCOUNT_ID)]["tools"][tool_type].append(config_data)
        
        # Save updated data
        with open(draft_file, 'w') as f:
            json.dump(draft_data, f, indent=2)
        
        logger.info(f"Tool configuration saved for {tool_type}")
        return f"✅ Tool configuration saved for {tool_type}"
    
    except Exception as e:
        logger.error(f"Error saving tool configuration: {str(e)}")
        return f"❌ Error saving tool configuration: {str(e)}"

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
    
    # Tool default configurations - each platform as a separate entry
    default_tools_config = {
        "BUSINESS_IDEAS_POST": [{"name": "Business Context", "config": {"enabled": True}}],
        "HOLIDAY_POST": [{"name": "Get Upcoming Holidays", "config": {"include_business_context": True}}],
        "REPURPOSED_POST": [{"name": "Get Top performing posts - all", "config": {
            "num_posts": 5,
            "evaluation_metric": "Engagement"
        }}],
        "COMP": [{"name": "Get Top performing posts - all", "config": {
            "num_posts": 5,
            "evaluation_metric": "Engagement"
        }}],
        "TRENDING": [{"name": "Fetch Trending Topics", "config": {"enabled": True}}]
    }
    
    prompts = {}
    sources = {}
    
    # Try to load existing draft to preserve tool configurations
    draft_file = f"drafts/{ACCOUNT_ID}.json"
    if os.path.exists(draft_file):
        with open(draft_file, 'r') as f:
            existing_draft_data = json.load(f)
        # Get existing tool configurations if they exist
        if str(ACCOUNT_ID) in existing_draft_data and "tools" in existing_draft_data[str(ACCOUNT_ID)]:
            tools = existing_draft_data[str(ACCOUNT_ID)]["tools"]
        else:
            tools = {}
    else:
        tools = {}
    
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
            
            # Add default tool configuration if none exists for this task
            if simple_tag not in tools and toggle_state:
                tools[simple_tag] = default_tools_config.get(simple_tag, [])
    
    # Create the final data structure
    draft_data = {
        f"{ACCOUNT_ID}": {
            "prompts": prompts,
            "sources": sources,
            "tools": tools
        }
    }
    
    # Save to file
    os.makedirs("drafts", exist_ok=True)
    filename = f"drafts/{ACCOUNT_ID}.json"
    
    with open(filename, "w") as f:
        json.dump(draft_data, f, indent=2)
    
    logger.info(f"Draft saved as {filename}")
    return f"✅ Draft saved as {filename}"

# Add functions for each tool save button
def save_holiday_config(get_business_context, get_upcoming_holidays):
    tool_config = {
        "name": "Get Upcoming Holidays",
        "config": {
            "include_business_context": bool(get_business_context)
        }
    }
    return save_tool_config("HOLIDAY_POST", tool_config)


def save_business_ideas_config(business_context):
    tool_config = {
        "name": "Business Context",
        "config": {
            "enabled": bool(business_context)
        }
    }
    return save_tool_config("BUSINESS_IDEAS_POST", tool_config)

def save_trending_topics_config(fetch_trending):
    tool_config = {
        "name": "Fetch Trending Topics",
        "config": {
            "enabled": bool(fetch_trending)
        }
    }
    return save_tool_config("TRENDING", tool_config)

def load_draft_for_account(account_id):
    """
    Load draft data for the specified account ID
    
    Args:
        account_id: The account ID to load drafts for
    
    Returns:
        Tuple of values for all form fields (toggles and prompts) and tool configurations
    """
    draft_file = f"drafts/{account_id}.json"
    logger.info(f"Attempting to load draft: {draft_file}")
    
    try:
        # Check if draft file exists
        if not os.path.exists(draft_file):
            logger.warning(f"No draft found for Account ID: {account_id}")
            return None  # Return None to indicate no draft was found
        
        # Load the draft data
        with open(draft_file, 'r') as f:
            draft_data = json.load(f)
        
        # Get the account data section
        account_data = draft_data.get(str(account_id), {})
        if not account_data:
            logger.warning(f"No data found for Account ID: {account_id} in draft file")
            return None
        
        # Extract prompts, sources, and tools
        prompts = account_data.get("prompts", {})
        sources_dict = account_data.get("sources", {})
        tools_dict = account_data.get("tools", {})
        
        print(" draft_data ------ ------ ----- ", prompts)
        # Mapping for tags to match the order in the UI
        tag_mapping = {
            "BUSINESS_IDEAS_POST": 0,  # Post ideas
            "HOLIDAY_POST": 1,         # Holiday ideas
            "REPURPOSED_POST": 2,      # My posts
            "COMP": 3,                 # Competitor posts
            "TRENDING": 4              # Trending
        }
        
        # Create default values for all fields
        toggle_values = [True] * 5
        prompt_values = [
            " Generate post ideas based on the business context.",
            " Generate post for upcoming holidays.",
            " Generate new posts based on your top performing posts.",
            " Generate new posts based on your top performing posts.",
            " Create posts based on the latest trends"
        ]
        
        # Update with values from the draft
        for tag, index in tag_mapping.items():
            if tag in sources_dict:
                toggle_values[index] = sources_dict[tag]
                
            if tag in prompts and prompts[tag]:
                # Use the first prompt in the list
                prompt_values[index] = prompts[tag][0]
        
        # Return toggle values, prompt values, and tool configurations
        return toggle_values + prompt_values, tools_dict
    
    except Exception as e:
        logger.error(f"Error loading draft: {str(e)}")
        return None

def update_account_id_and_load_draft(new_account_id):
    """Update the global account ID and load draft data"""
    global ACCOUNT_ID
    try:
        logger.info(f"Updating account ID to: {new_account_id}")
        ACCOUNT_ID = new_account_id
        set_key(".env", "ACCOUNT_ID", ACCOUNT_ID)
        logger.info(f"Account ID updated to: {ACCOUNT_ID}")
        
        # Try to load draft data for this account
        draft_result = load_draft_for_account(ACCOUNT_ID)
        
        if draft_result:
            draft_values, tools_dict = draft_result
            
            # Create an update object for each toggle and prompt
            updates = []
            for i, val in enumerate(draft_values):
                print("val ------     /////// /-------", val)
                updates.append(gr.update(value=val))
            
            print("updates ------ ------ ----- ", updates)
            
            # Return success message and form values
            return (
                f"✅ Account ID updated to: {ACCOUNT_ID}. Draft loaded.",
                gr.update(visible=False),
                *updates
            )
        else:
            # Return success message without changing form values
            return (
                f"✅ Account ID updated to: {ACCOUNT_ID}. No draft found.",
                gr.update(visible=False),
                *[gr.update() for _ in range(10)]  # 5 toggles + 5 prompts
            )
    except ValueError:
        logger.error("Invalid account ID entered.")
        return (
            "❌ Please enter a valid numeric account ID",
            gr.update(visible=True),
            *[gr.update() for _ in range(10)]  # 5 toggles + 5 prompts
        )
    
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
        
        # Get prompts, sources, and tools from the draft
        prompts = account_data.get("prompts", {})
        sources_dict = account_data.get("sources", {})
        tools_dict = account_data.get("tools", {})
        
        # Create list of enabled sources
        sources = [key for key, enabled in sources_dict.items() if enabled]
        
        load_dotenv(override=True)
        total_post = os.environ.get("POSTS_PER_WEEK", "7")
        # Create the API payload
        payload = {
            "account_id": ACCOUNT_ID,
            "total_post": int(total_post), 
            "small_id": "1148914",
            "long_id": "169030216166956",
            "business_name": "Village Pet Care",
            "holidays": [
                {"date": "2025-03-09", "holiday": "Diwali"},
                {"date": "2025-03-17", "holiday": "St. Patrick's Day"}
            ],
            "number_of_days": 10,
            "categories": sources,
            "prompt_config": prompts,
            "tools_config": tools_dict  # Add tools configuration to the payload
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

# === Placeholder for tag button logic ===
def tag_clicked(tag_label):
    logger.info(f"[Tag clicked]: {tag_label}")
    return

def open_tools_modal():
    logger.info("Opening tools modal.")
    return (
        gr.update(visible=True),   # tools_modal
        gr.update(visible=False),  # holiday_detail_view
        gr.update(visible=False),  # business_posts_detail_view
        gr.update(visible=False),  # competitor_posts_detail_view
        gr.update(visible=False),  # business_ideas_detail_view
        gr.update(visible=False)   # trending_topics_detail_view
    )

def close_tools_modal():
    logger.info("Closing tools modal.")
    return (
        gr.update(visible=False),  # tools_modal
        gr.update(visible=False),  # holiday_detail_view
        gr.update(visible=False),  # business_posts_detail_view
        gr.update(visible=False),  # competitor_posts_detail_view
        gr.update(visible=False),  # business_ideas_detail_view
        gr.update(visible=False)   # trending_topics_detail_view
    )

# === Close tool detail view ===
def close_tool_detail():
    logger.info("Closing tool detail view.")
    return gr.update(visible=False), gr.update(visible=True)

# === Open tool detail view ===
def open_tool_detail(tool_name):
    logger.info(f"Opening tool detail for: {tool_name}")
    return gr.update(visible=True), gr.update(visible=False)

# === Show/hide the prompt block ===
def toggle_task(enabled):
    logger.info(f"Toggling task block to: {enabled}")
    return gr.update(visible=enabled)

# Functions for tool detail views
def open_holiday_detail():
    return gr.update(visible=True), gr.update(visible=False)

def open_business_posts_detail():
    return gr.update(visible=True), gr.update(visible=False)

def open_competitor_posts_detail():
    return gr.update(visible=True), gr.update(visible=False)

def open_business_ideas_detail():
    return gr.update(visible=True), gr.update(visible=False)

def open_trending_topics_detail():
    return gr.update(visible=True), gr.update(visible=False)

def close_all_tool_details():
    return (
        gr.update(visible=False),  # holiday
        gr.update(visible=False),  # business posts
        gr.update(visible=False),  # competitor posts
        gr.update(visible=False),  # business ideas
        gr.update(visible=False),  # trending topics
        gr.update(visible=True)    # tools modal
    )

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
    global tools_modal, holiday_detail_view, business_posts_detail_view, competitor_posts_detail_view, business_ideas_detail_view, trending_topics_detail_view

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
            width: 100%; /* Make it full width */
        }
        
        .light-prompt-box textarea {
            background-color: #f5f5f5 !important;
            border: none !important;
            border-radius: 6px !important;
            padding: 10px !important;
            padding-right: 105px !important;
            font-size: 14px !important;
            min-height: 80px !important;
            max-width: calc(100% - 105px) !important; /* Try max-width instead of width */
            box-sizing: border-box !important;
        }

        /* Additional selector to increase specificity */
        .gradio-container .light-prompt-box textarea {
            padding-right: 110px !important;
            max-width: calc(100%) !important;
        }

        /* Force text to wrap */
        .light-prompt-box textarea {
            white-space: pre-wrap !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
        }
        
        .tools-btn {
            position: absolute;
            top: 10px;
            right: 20px;        /* Increased from 10px to 20px to move it further from the edge */
            background: none;
            border: none;
            color: #1a73e8;
            font-size: 14px;
            padding: 6px 10px;
            cursor: pointer;
            z-index: 10;
            opacity: 0.8;
            border-radius: 4px;
            height: 25px; /* Set a fixed height */
            width: 105px; /* Set a fixed width */
        }

        .tools-btn:hover {
            background-color: #f0f7ff;  /* Light blue background on hover */
            opacity: 1;
        }
        
        .tools-btn:hover {
            opacity: 1;
            background-color: #f0f7ff;
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
        
        #tool-detail-view {
            position: fixed;
            top: 0;
            right: 0;
            bottom: 0;
            width: 520px;
            background-color: white;
            box-shadow: -4px 0 12px rgba(0,0,0,0.1);
            padding: 0;
            z-index: 1001;
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
        
        /* Tool detail view styling */
        .tool-detail-content {
            padding: 20px;
        }
        
        .tool-detail-header {
            margin-bottom: 20px;
        }
        
        .tool-detail-title {
            font-size: 18px;
            font-weight: 500;
            margin-bottom: 8px;
        }
        
        .tool-detail-description {
            color: #5f6368;
            font-size: 14px;
        }
        
        .tool-detail-section {
            margin-bottom: 24px;
        }
        
        .tool-detail-section-title {
            font-size: 16px;
            font-weight: 500;
            margin-bottom: 12px;
            color: #3c4043;
        }
        
        .form-group {
            margin-bottom: 16px;
        }
        
        .form-label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            font-size: 14px;
        }
        
        .form-control {
            width: 100%;
            padding: 10px;
            border: 1px solid #dadce0;
            border-radius: 4px;
            font-size: 14px;
        }
        
        .form-helper {
            font-size: 12px;
            color: #5f6368;
            margin-top: 4px;
        }
        
        .tool-action-buttons {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            margin-top: 24px;
        }
        
        .cancel-btn {
            background-color: white;
            border: 1px solid #dadce0;
            color: #3c4043;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 500;
            cursor: pointer;
        }
        
        .save-btn {
            background-color: #1a73e8;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 500;
            cursor: pointer;
        }
        
        .save-btn:hover {
            background-color: #1558b0;
        }
        
        .cancel-btn:hover {
            background-color: #f1f3f4;
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
            
            # Tool categories
            gr.HTML("""
            <div class="tools-section-header">
                <h4>Select a tool to configure</h4>
            </div>
            """)
            
            # Tool list items
            with gr.Column(elem_classes=["tools-list"]):
                holiday_btn = gr.Button("Holiday", elem_classes=["tool-item-btn"])
                business_posts_btn = gr.Button("Business Top performing Posts", elem_classes=["tool-item-btn"])
                competitor_posts_btn = gr.Button("Competitor Top performing Posts", elem_classes=["tool-item-btn"])
                business_ideas_btn = gr.Button("Business Ideas / Post Ideas", elem_classes=["tool-item-btn"])
                trending_topics_btn = gr.Button("Trending Topics", elem_classes=["tool-item-btn"])

    

    # Tool detail view for Holiday
    with gr.Group(visible=False, elem_id="tool-detail-view-holiday") as holiday_detail_view:
        with gr.Column():
            with gr.Row(elem_classes=["tools-header"]):
                back_button_holiday = gr.Button("←", elem_classes=["back-button"])
                gr.HTML("<h3>Configure Holiday Tool</h3>")
                close_holiday_detail_btn = gr.Button("×", elem_classes=["tools-close"])
            
            with gr.Column(elem_classes=["tool-detail-content"]):
                gr.HTML("""
                <div class="tool-detail-title">Holiday</div>
                <div class="tool-detail-description">
                    Configure holiday-related tools to create posts based on upcoming holidays.
                </div>
                """)
                
                with gr.Column(elem_classes=["tool-detail-section"]):
                    gr.HTML("<div class='tool-detail-section-title'>Required Tools</div>")
                    
                    get_business_context = gr.Checkbox(label="Get Business Context", value=True)
                    get_upcoming_holidays = gr.Checkbox(label="Get Upcoming Holidays", value=True)
                    
                    gr.HTML("<p class='form-helper'>Note: 'Get Upcoming Holidays' is mandatory</p>")
                
                holiday_save_btn = gr.Button("Save Configuration", variant="primary", elem_classes=["save-btn"])

    # Tool detail view for Business Top Performing Posts
    with gr.Group(visible=False, elem_id="tool-detail-view-business-posts") as business_posts_detail_view:
        with gr.Column():
            with gr.Row(elem_classes=["tools-header"]):
                back_button_business = gr.Button("←", elem_classes=["back-button"])
                gr.HTML("<h3>Configure Business Posts Tool</h3>")
                close_business_posts_detail_btn = gr.Button("×", elem_classes=["tools-close"])
            
            with gr.Column(elem_classes=["tool-detail-content"]):
                gr.HTML("""
                <div class="tool-detail-title">Business Top Performing Posts</div>
                <div class="tool-detail-description">
                    Configure tools to analyze and leverage your business's top performing posts.
                </div>
                """)
                
                with gr.Column(elem_classes=["tool-detail-section"]):
                    gr.HTML("<div class='tool-detail-section-title'>Select Platforms</div>")
                    
                    get_all_business_posts = gr.Checkbox(label="Get Top performing posts - all", value=True)
                    get_facebook_business_posts = gr.Checkbox(label="Get Top performing posts - Facebook", value=False)
                    get_twitter_business_posts = gr.Checkbox(label="Get Top performing posts - Twitter", value=False)
                    get_instagram_business_posts = gr.Checkbox(label="Get Top performing posts - Instagram", value=False)
                    
                    gr.HTML("<p class='form-helper'>Note: At least one option must be selected</p>")
                
                with gr.Column(elem_classes=["tool-detail-section"]):
                    gr.HTML("<div class='tool-detail-section-title'>Configuration</div>")
                    
                    num_business_posts = gr.Slider(minimum=1, maximum=20, value=5, step=1, label="Number of posts")
                    business_posts_metric = gr.Radio(
                        choices=["Engagement", "Impression"], 
                        value="Engagement", 
                        label="Evaluation Metric"
                    )
                
                business_posts_save_btn = gr.Button("Save Configuration", variant="primary", elem_classes=["save-btn"])

    # Tool detail view for Competitor Top Performing Posts
    with gr.Group(visible=False, elem_id="tool-detail-view-competitor-posts") as competitor_posts_detail_view:
        with gr.Column():
            with gr.Row(elem_classes=["tools-header"]):
                back_button_competitor = gr.Button("←", elem_classes=["back-button"])
                gr.HTML("<h3>Configure Competitor Posts Tool</h3>")
                close_competitor_posts_detail_btn = gr.Button("×", elem_classes=["tools-close"])
            
            with gr.Column(elem_classes=["tool-detail-content"]):
                gr.HTML("""
                <div class="tool-detail-title">Competitor Top Performing Posts</div>
                <div class="tool-detail-description">
                    Configure tools to analyze and leverage competitors' top performing posts.
                </div>
                """)
                
                with gr.Column(elem_classes=["tool-detail-section"]):
                    gr.HTML("<div class='tool-detail-section-title'>Select Platforms</div>")
                    
                    get_all_competitor_posts = gr.Checkbox(label="Get Top performing posts - all", value=True)
                    get_facebook_competitor_posts = gr.Checkbox(label="Get Top performing posts - Facebook", value=False)
                    get_twitter_competitor_posts = gr.Checkbox(label="Get Top performing posts - Twitter", value=False)
                    get_instagram_competitor_posts = gr.Checkbox(label="Get Top performing posts - Instagram", value=False)
                    
                    gr.HTML("<p class='form-helper'>Note: At least one option must be selected</p>")
                
                with gr.Column(elem_classes=["tool-detail-section"]):
                    gr.HTML("<div class='tool-detail-section-title'>Configuration</div>")
                    
                    num_competitor_posts = gr.Slider(minimum=1, maximum=20, value=5, step=1, label="Number of posts")
                    competitor_posts_metric = gr.Radio(
                        choices=["Engagement", "Impression"], 
                        value="Engagement", 
                        label="Evaluation Metric"
                    )
                
                competitor_posts_save_btn = gr.Button("Save Configuration", variant="primary", elem_classes=["save-btn"])

    # Tool detail view for Business Ideas / Post Ideas
    with gr.Group(visible=False, elem_id="tool-detail-view-business-ideas") as business_ideas_detail_view:
        with gr.Column():
            with gr.Row(elem_classes=["tools-header"]):
                back_button_ideas = gr.Button("←", elem_classes=["back-button"])
                gr.HTML("<h3>Configure Business Ideas Tool</h3>")
                close_business_ideas_detail_btn = gr.Button("×", elem_classes=["tools-close"])
            
            with gr.Column(elem_classes=["tool-detail-content"]):
                gr.HTML("""
                <div class="tool-detail-title">Business Ideas / Post Ideas</div>
                <div class="tool-detail-description">
                    Configure tools to generate business and post ideas.
                </div>
                """)
                
                with gr.Column(elem_classes=["tool-detail-section"]):
                    gr.HTML("<div class='tool-detail-section-title'>Required Tools</div>")
                    
                    business_context = gr.Checkbox(label="Business Context", value=True, interactive=False)
                    
                    gr.HTML("<p class='form-helper'>Note: 'Business Context' is mandatory and cannot be disabled</p>")
                
                business_ideas_save_btn = gr.Button("Save Configuration", variant="primary", elem_classes=["save-btn"])

    # Tool detail view for Trending Topics
    with gr.Group(visible=False, elem_id="tool-detail-view-trending") as trending_topics_detail_view:
        with gr.Column():
            with gr.Row(elem_classes=["tools-header"]):
                back_button_trending = gr.Button("←", elem_classes=["back-button"])
                gr.HTML("<h3>Configure Trending Topics Tool</h3>")
                close_trending_topics_detail_btn = gr.Button("×", elem_classes=["tools-close"])
            
            with gr.Column(elem_classes=["tool-detail-content"]):
                gr.HTML("""
                <div class="tool-detail-title">Trending Topics</div>
                <div class="tool-detail-description">
                    Configure tools to discover and leverage trending topics.
                </div>
                """)
                
                with gr.Column(elem_classes=["tool-detail-section"]):
                    gr.HTML("<div class='tool-detail-section-title'>Required Tools</div>")
                    
                    fetch_trending_topics = gr.Checkbox(label="Fetch Trending Topics", value=True, interactive=False)
                    
                    gr.HTML("<p class='form-helper'>Note: 'Fetch Trending Topics' is mandatory and cannot be disabled</p>")
                
                trending_topics_save_btn = gr.Button("Save Configuration", variant="primary", elem_classes=["save-btn"])
            
    # Add click events for each tool button to open detail view
    holiday_btn.click(
        fn=open_holiday_detail,
        outputs=[holiday_detail_view, tools_modal]
    )

    business_posts_btn.click(
        fn=open_business_posts_detail,
        outputs=[business_posts_detail_view, tools_modal]
    )

    competitor_posts_btn.click(
        fn=open_competitor_posts_detail,
        outputs=[competitor_posts_detail_view, tools_modal]
    )

    business_ideas_btn.click(
        fn=open_business_ideas_detail,
        outputs=[business_ideas_detail_view, tools_modal]
    )

    trending_topics_btn.click(
        fn=open_trending_topics_detail,
        outputs=[trending_topics_detail_view, tools_modal]
    )

    # Back buttons for each tool detail view
    back_button_holiday.click(
        fn=close_all_tool_details,
        outputs=[
            holiday_detail_view, 
            business_posts_detail_view, 
            competitor_posts_detail_view, 
            business_ideas_detail_view, 
            trending_topics_detail_view, 
            tools_modal
        ]
    )

    back_button_business.click(
        fn=close_all_tool_details,
        outputs=[
            holiday_detail_view, 
            business_posts_detail_view, 
            competitor_posts_detail_view, 
            business_ideas_detail_view, 
            trending_topics_detail_view, 
            tools_modal
        ]
    )

    back_button_competitor.click(
        fn=close_all_tool_details,
        outputs=[
            holiday_detail_view, 
            business_posts_detail_view, 
            competitor_posts_detail_view, 
            business_ideas_detail_view, 
            trending_topics_detail_view, 
            tools_modal
        ]
    )

    back_button_ideas.click(
        fn=close_all_tool_details,
        outputs=[
            holiday_detail_view, 
            business_posts_detail_view, 
            competitor_posts_detail_view, 
            business_ideas_detail_view, 
            trending_topics_detail_view, 
            tools_modal
        ]
    )

    back_button_trending.click(
        fn=close_all_tool_details,
        outputs=[
            holiday_detail_view, 
            business_posts_detail_view, 
            competitor_posts_detail_view, 
            business_ideas_detail_view, 
            trending_topics_detail_view, 
            tools_modal
        ]
    )

    # Close buttons for each tool detail view
    close_holiday_detail_btn.click(
        fn=close_all_tool_details,
        outputs=[
            holiday_detail_view, 
            business_posts_detail_view, 
            competitor_posts_detail_view, 
            business_ideas_detail_view, 
            trending_topics_detail_view, 
            tools_modal
        ]
    )

    close_business_posts_detail_btn.click(
        fn=close_all_tool_details,
        outputs=[
            holiday_detail_view, 
            business_posts_detail_view, 
            competitor_posts_detail_view, 
            business_ideas_detail_view, 
            trending_topics_detail_view, 
            tools_modal
        ]
    )

    close_competitor_posts_detail_btn.click(
        fn=close_all_tool_details,
        outputs=[
            holiday_detail_view, 
            business_posts_detail_view, 
            competitor_posts_detail_view, 
            business_ideas_detail_view, 
            trending_topics_detail_view, 
            tools_modal
        ]
    )

    close_business_ideas_detail_btn.click(
        fn=close_all_tool_details,
        outputs=[
            holiday_detail_view, 
            business_posts_detail_view, 
            competitor_posts_detail_view, 
            business_ideas_detail_view, 
            trending_topics_detail_view, 
            tools_modal
        ]
    )

    close_trending_topics_detail_btn.click(
        fn=close_all_tool_details,
        outputs=[
            holiday_detail_view, 
            business_posts_detail_view, 
            competitor_posts_detail_view, 
            business_ideas_detail_view, 
            trending_topics_detail_view, 
            tools_modal
        ]
    )            

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
    
    # Open tools modal
    tools_btn_list = []
    
    # Close tools modal
    close_tools_btn.click(
        fn=close_tools_modal,
        outputs=[
            tools_modal, 
            holiday_detail_view, 
            business_posts_detail_view, 
            competitor_posts_detail_view, 
            business_ideas_detail_view, 
            trending_topics_detail_view
        ]
    )
    
    # Add save button handlers for tool configurations
    holiday_save_btn.click(
        fn=save_holiday_config,
        inputs=[get_business_context, get_upcoming_holidays],
        outputs=[status_message]
    )

    business_posts_save_btn.click(
        fn=save_business_posts_config,
        inputs=[
            get_all_business_posts, 
            get_facebook_business_posts, 
            get_twitter_business_posts, 
            get_instagram_business_posts,
            num_business_posts,
            business_posts_metric
        ],
        outputs=[status_message]
    )

    competitor_posts_save_btn.click(
        fn=save_competitor_posts_config,
        inputs=[
            get_all_competitor_posts, 
            get_facebook_competitor_posts, 
            get_twitter_competitor_posts, 
            get_instagram_competitor_posts,
            num_competitor_posts,
            competitor_posts_metric
        ],
        outputs=[status_message]
    )

    business_ideas_save_btn.click(
        fn=save_business_ideas_config,
        inputs=[business_context],
        outputs=[status_message]
    )

    trending_topics_save_btn.click(
        fn=save_trending_topics_config,
        inputs=[fetch_trending_topics],
        outputs=[status_message]
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
                                    # elem_id=f"main-prompt-{i}"
                                )
                                tools_btn = gr.Button("🔧 Tools", elem_classes=["tools-btn"])
                                tools_btn_list.append(tools_btn)
                                tools_btn.click(
                                    fn=open_tools_modal,
                                    outputs=[
                                        tools_modal, 
                                        holiday_detail_view, 
                                        business_posts_detail_view, 
                                        competitor_posts_detail_view, 
                                        business_ideas_detail_view, 
                                        trending_topics_detail_view
                                    ]
                                )
                            all_main_prompts.append(main_prompt)
                        
                        # tag_btn = gr.Button(f"⚙️ {tag}", size="sm", scale=2)
                        # tag_btn.click(fn=lambda t=tag: tag_clicked(t), outputs=[])

                    # For extra prompts
                    prompt_count = gr.State(0)
                    extra_prompts_containers = []
                    extra_prompts = []
                    
                    for j in range(3):
                        with gr.Group(visible=False, elem_classes=["light-prompt-box"]) as extra_container:
                            extra_prompt = gr.Textbox(
                                placeholder="New prompt...",
                                interactive=True,
                                show_label=False,
                                lines=2
                            )
                            extra_tools_btn = gr.Button("🔧 Tools", elem_classes=["tools-btn"])
                            extra_tools_btn.click(
                                fn=open_tools_modal,
                                outputs=[
                                    tools_modal, 
                                    holiday_detail_view, 
                                    business_posts_detail_view, 
                                    competitor_posts_detail_view, 
                                    business_ideas_detail_view, 
                                    trending_topics_detail_view
                                ]
                            )
                            extra_prompts.append(extra_prompt)
                            extra_prompts_containers.append(extra_container)
                    
                    all_extra_prompts.extend(extra_prompts)
                    
                    add_btn = gr.Button("➕ Add prompt", size="sm", elem_classes=["add-prompt-btn"])
                    add_btn.click(
                        add_prompt,
                        inputs=[prompt_count],
                        outputs=[prompt_count] + extra_prompts_containers
                    )

                toggle.change(
                    fn=toggle_task,
                    inputs=[toggle],
                    outputs=[content_block]
                )
    
    print("all_toggles ------ ------ ----- ", all_toggles)
    print("all_main_prompts ------ ------ ----- ", all_main_prompts)
    # Save settings
    save_settings_btn.click(
        fn=update_account_id_and_load_draft,
        inputs=[account_id_input],
        outputs=[settings_status, settings_modal] + all_toggles + all_main_prompts
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