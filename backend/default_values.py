from enum import Enum

from langchain_core.tools import tool
# from numpy.distutils.conv_template import header
from pydantic import BaseModel, Field
from typing import Annotated, Literal, List, Dict, Any, Optional
from datetime import datetime, timedelta
from typing import Dict, List

import requests
import json


PIXABAY_API_KEY = "50243041-2741613e433c3c2a3b1783510"

# businessId='1160473'

holiday_system_prompt = '''
Post should be in English language only. Balance information about the business and the event. 
Incorporate a connection between the business and the historical event. 
Avoid any time-specific language or references to specific dates. 
Use <|BUSINESS_NAME|> tag in same format given. Do not change it, use as it is. Be creative.
'''

general_system_prompt = '''
You're a Social Media Writer. Below are some things to keep in mind.
Post should be in English language only. Balance information about the business and the event. 
Incorporate a connection between the business and the historical event. 
Avoid any time-specific language or references to specific dates.
Avoid vague references like Your local shop at some location. 
Use <|BUSINESS_NAME|> tag whenever referencing the business or its location. Do not change it, use as it is.
Be creative.
'''

business_context_prompt = '''
Use the Business details for context
<Business Details>
{businessDetails}
</Business Details>
'''

keyword_generator_system = '''
After writing the post, generate relevant keywords for the post.
The goal is to identify words or phrases which describe this post and would be highly suitable for searching images on a stock photo website. 
Keep the keywords/phrases as a simple string separated by spaces.
To complete this task, follow these guidelines:
1. Prioritize concrete objects, scenes, or concepts that can be easily depicted in images.
2. Select words that capture the main theme or subject of the text.
'''

tools_prompt = '''
You have access to the below tools:
1. get_business_meta: Use this tool if there is no business context. You can get information about the business using this tool.
2. get_upcoming_week_holidays: Use this tool to get the upcoming holidays given the number of days to look for in the future.
'''

business_idea_system = '''
You are a social media content creator for a business. 
Your task is to generate only {num} social media post headers and their corresponding posts based on the provided business details. 

Here are the business details:
<business_details>\n{business_details}\n</business_details>

Your goal is to create engaging and relevant social media content for this business. 
Follow these guidelines:
1. Be creative and engaging.
2. Write the post content in English only, using only English words
3. Keep the tone friendly and inviting
4. Do not generate about dates/number of years
5. Use <|BUSINESS_NAME|> tag in same format given. Do not change it, use as it is.
'''

repurposed_post_system = '''
You are a social media content writer. Rephrase the given social media post for the business based on the provided original post.
<original post>\n{post}\n</original_post>

Instructions: 
1. Rephrase the post based on the given content. 
2. Ensure the rephrased post is of similar length to the original post. 
3. Avoid fabricating information. 
4. Include the business name wherever relevant. 
5. Rephrase posts only for the specified services and avoid assumptions or fabrications. 
6. Be very very careful of not adding any extra information from your side Ensure you strictly follow the above instructions and do not rephrase posts with offers (e.g., 30% off, starting at just $$), season-specific content, or years. 
7. Cross-verify that the rephrased post information matches the information given in the original post. If the information does not match, rephrase the post with the correct information. 
8. Do not provide any misleading information (e.g., thousands of happy customers).
'''

default_user_prompt = '''
Keep the system instructions in mind. Below are some special instructions requested by the user, separated by new line. If any conflicting instructions occur, prioritise the system instructions. If you cannot follow some instructions, then ignore that and inside <error_message> you can output why you couldn't follow some instruction if any.\n
'''

competitor_system_prompt = '''
You are a social media content writer/post creator. Your task is to create social media posts for a business using the content from competitors' posts.
Objectives:
To create proper posts which drives value to the business and its customers.
To strictly follow the instructions given mentioned below and give preferences to the user instructions if any.
Instructions:
1. Create {count} social media posts using content from competitors for the given business.
2. Check the tool catalog for the definition and use the appropriate tool to fetch the data. Business name and tools to invoke.
```Business Name: {business_name}, Tools: {tools_list}
3. Use the config {config} for each tool on specific constraints strictly for further analysis. Follow the filtering in the same order below.
 duration - based on published date filter latest posts till specified duration-> evaluation metric for posts -> num_posts - no of posts to fetch for analysis. 
4. From the fetched posts, evaluate and classify each post using the following rules:
<useful> - if the post content is reusable or adaptable for future business posts.
<useless> -  if it is highly specific (e.g., direct promotions, personal wishes, staff announcements).
<failure> -  if the post content is missing or unreadable.
Only proceed with posts marked as <useful> for further content generation tailored to the business {business_name}.
After all analysis, proceed with filtered final set of data.
5. Before generating the posts, provide intermediate steps of what all data you are fetching after above steps before you are generating posts.
should include tool name, number of posts in a tool, published date, evaluation metric only.
<tool_name><filtered_date_list_taken_finally><evaluation_metric_list><number_of_posts_per_tool>
<print the filtered intermediate data> used for analysis. This is just for intermediate step to verify filtered data is inline with config.
6. After analysis, generate the posts using the filtered data and output strictly in the below format {format_instructions_list} if no posts are available, just return empty list in the final output format.
'''


class PostType(Enum):
    HOLIDAY_POST = 1
    REPURPOSED_POST = 3
    COMP = 2
    TRENDING = 4
    BUSINESS_IDEAS_POST = 5


@tool
def get_business_meta(businessId):
    """
    Takes in the businessId and returns information about the business like category, services, products, etc.
    :param businessId
    :return: business category as string and JSON of business metadata
    """
    url = "https://corebusiness.birdeye.com/v1/business/profile/basic-info"

    payload = {}
    headers = {
      'accept': '*/*',
      'account-id': str(businessId)
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    business_json = json.loads(response.text)
    return business_json.pop('category'), business_json


class Holiday_input(BaseModel):
    category: Optional[str] = ""
    subCategories: Optional[list] = []
    keywords: Optional[list] = []
    products: Optional[list] = []
    services: Optional[list] = []
    description: Optional[str] = ""
    name: Optional[str] = ""
    holiday: str = ""
    country: Optional[str] = ""
    date: Optional[str] = ""
    channel: Optional[str] = ""
    extraParams: dict = dict()


def call_holiday_gen(payload):
    url = "http://0.0.0.0:8080/api/v1/social/generate-post-using-holiday/"

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return json.loads(response.text)


def search_pixabay_images(query, image_type='photo', per_page=5):
    try:
        base_url = 'https://pixabay.com/api/'
        params = {
            'key': PIXABAY_API_KEY, # temp key
            'q': query,
            'image_type': image_type,
            'per_page': per_page
        }
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        res = response.json()
        images = [i['largeImageURL'] for i in res['hits']]
        return images
    except:
        return []


def fetch_business_competitors_trends(trends=False):
    if not trends:
        with open("competitors_mock.json","r") as f:
            competitors_data = json.load(f)
            print(len(competitors_data))
        return competitors_data
    else:
        with open("competitors_mock.json","r") as f:
            competitors_data = json.load(f)
            print(len(competitors_data))
        return competitors_data


def fetch_all_holidays():
    url = "https://socialapi.birdeye.com/social/post/261968/calendar/events"

    payload = json.dumps({
        "year": 2025
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return json.loads(response.text)

@tool
def get_upcoming_week_holidays(days=7) -> List[Dict[str, str]]:
    """
    Takes in the number of upcoming days and returns all the events and holidays in that timeframe starting from current day.
    :param days: This is the upcoming number of days that we need to check for any Holidays
    :return: List of objects with date and Holiday/Event name as attributes.
    """
    payload = fetch_all_holidays()
    today = datetime.today().date()
    end_date = today + timedelta(days=days)

    upcoming = []
    for event in payload.get("events", []):
        try:
            event_date = datetime.strptime(event["eventDate"], "%Y-%m-%d").date()
            if today <= event_date <= end_date:
                upcoming.append({
                    "date": event["eventDate"],
                    "holiday": event["eventName"]
                })
        except ValueError:
            continue  # skip if date is malformed

    return upcoming


def get_repurposed_posts(enterpriseId, count):
    url = 'http://socialapi.birdeye.com/social/ai/get/posts'
    payload = {
        "numberOfPosts": count,
        "enterpriseId": enterpriseId
    }

    headers = {
        'Content-Type': 'application/json'
    }

    # response = requests.request("POST", url, headers=headers, data=payload)
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    return json.loads(response.text)['postDetailsDTOS']


def fetch_btp():
    url = "https://app.birdeye.com/resources/v1/api/social/post/best/time/per-day"

    payload = json.dumps({
        "calendarView": "day",
        "channels": []
    })
    headers = {
        'Accept': 'application/json',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'https://app.birdeye.com',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'X-Bazaarify-Session-Token': '3048934a-3ba7-4a38-8017-1269e1dd0766',
        'X-Business-Id': '261968',
        'X-Business-businessNumber': '149546071353527',
        'X-User-Id': '2730332',
        'account-id': '261968',
        'business-type': 'Enterprise-Location',
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'user-email': 'manish.kumar2@birdeye.com'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return json.loads(response.text)


def get_best_time_slots_next_7_days(time_slots: Dict[str, List[str]], total_count: int) -> List[Dict[str, str]]:
    today = datetime.today().date()
    end_date = today + timedelta(days=6)

    # Step 1: Parse and filter the dates within the next 7 days
    valid_slots = []
    for date_str, times in time_slots.items():
        try:
            dt = datetime.strptime(date_str, "%m/%d/%Y").date()
            if today <= dt <= end_date:
                for time in sorted(times):  # sort times in day
                    valid_slots.append({"date": dt, "time": time})
        except ValueError:
            continue  # skip invalid dates

    # Step 2: Sort by date and time
    valid_slots.sort(key=lambda x: (x["date"], x["time"]))

    # Step 3: Fill unique dates first
    used_dates = set()
    final_slots = []

    for slot in valid_slots:
        if slot["date"] not in used_dates:
            final_slots.append(slot)
            used_dates.add(slot["date"])
        if len(final_slots) == total_count:
            return format_slots(final_slots)

    # Step 4: Fill remaining from repeated dates if needed
    for slot in valid_slots:
        if len(final_slots) == total_count:
            break
        if final_slots.count(slot) < valid_slots.count(slot):  # avoid exact duplicates
            final_slots.append(slot)

    return format_slots(final_slots)


def format_slots(slots: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [{"date": slot["date"].strftime("%Y-%m-%d"), "time": slot["time"]} for slot in slots]


### Tool to fetch competitors data########
@tool
def fetch_business_competitors_all(business_name: str) -> Dict[str, Any]:
    """Fetches competitors data for a given business name and other filters if applicable in the given instruction
     publisheddata will be in epoch time format use it accordingly.
    """
    with open("competitors_mock.json", "r") as f:
        competitors_data = json.load(f)
        if business_name in competitors_data:
            competitors_data = competitors_data[business_name]
            return f"Below is the competitors data {competitors_data}"
    return "No Data Found"

@tool
def fetch_business_competitors_facebook(business_name: str) -> Dict[str, Any]:
    """Fetches competitors data for a given business name and channel 'Facebook'
    publisheddata will be in epoch time format use it accordingly.
    """
    with open("competitors_mock.json", "r") as f:
        competitors_data = json.load(f)
        if business_name in competitors_data:
            posts = competitors_data.get(business_name, {}).get("postData", [])
            results = [post for post in posts if post.get("channel") == "facebook"]
            return f"Below is the competitors data {results}"
    return "No Data Found"
@tool
def fetch_business_competitors_instagram(business_name: str) -> Dict[str, Any]:
    """Fetches competitors data for a given business name  and platform 'Instagram'
     publisheddata will be in epoch time format use it accordingly.
    """
    with open("competitors_mock.json", "r") as f:
        competitors_data = json.load(f)
        if business_name in competitors_data:
            posts = competitors_data.get(business_name, {}).get("postData", [])
            results = [post for post in posts if post.get("channel") == "instagram"]
            return f"Below is the competitors data {results}"
    return "No Data Found"

# @tool
# def fetch_business_trends(business_category: str) -> Dict[str, Any]:
#     "Fetches business trends data for a given business category and other filters if applicable in the given instruction"
#     with open("business_trends_mock.json", "r") as f:
#         trends_data = json.load(f)
#         if business_category in trends_data:
#             trends_data = trends_data[business_category]
#             return f"Below is the trends data data {trends_data}"
#     return "No data found"

TOOLS_REGISTRY = {
    "Get Top performing posts - facebook":{
        "function":fetch_business_competitors_facebook,
        "description":"Fetches top performing posts for a given business name and channel 'Facebook'."
    },
    "Get Top performing posts - instagram":{
        "function":fetch_business_competitors_instagram,
        "description":"Fetches top performing posts for a given business name and channel 'Instagram'."
    }
}

@tool
def fetch_business_trends(
        business_name: str,
        industry: str,
        sub_industry: str,
        recency: int,
        country: str = "US",
        city: str = "All Cities",
        state: str = "All States"
) -> List[str]:
    """
    Calls the local FastAPI endpoint to generate trending topics based on business and location context.
    """
    payload = {
        "business_name": business_name,
        "industry": industry,
        "sub_industry": sub_industry,
        "country": country,
        "city": city,
        "state": state,
        "recency": recency
    }
    try:
        response = requests.post("http://127.0.0.1:8008/generate-trending-topics", json=payload)
        response.raise_for_status()
        return response.json()  # Returns full JSON content
    except requests.RequestException as e:
        return {"error": str(e)}