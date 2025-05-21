from enum import Enum

from langchain_core.tools import tool
# from numpy.distutils.conv_template import header
from pydantic import BaseModel, Field
from typing import Annotated, Literal, List, Dict, Any, Optional
from datetime import datetime, timedelta
from typing import Dict, List

import requests
import json

import os
from enum import Enum
import re

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt.tool_node import msg_content_output
from pydantic import BaseModel, Field
from typing import Annotated, Literal, List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from typing import Dict, List


from datetime import datetime, date




PIXABAY_API_KEY = "50243041-2741613e433c3c2a3b1783510"

# businessId='1160473'

holiday_system_prompt = '''
Incorporate a connection between the business and the historical event if you have business context available.
Your task is generate social media posts based on the holiday or event mentioned.
'''

general_system_prompt = '''
You're a Social Media Writer. Below are some things to keep in mind.
Post should be in English language only. Balance information about the business and the event. 
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
1. Max 5 keywords should be generated/selected.
2. Prioritize concrete objects, scenes, or concepts that can be easily depicted in images.
3. Select words that capture the main theme or subject of the text.
'''

tools_prompt = '''
You have access to the below tools:
1. get_business_meta: Use this tool if there is no business context. You can get information about the business using this tool.
2. get_upcoming_week_holidays: Use this tool to get the upcoming holidays given the number of days to look for in the future.
'''

tools_repurpose_prompt = '''
You have access to the below tools:
1. get_useful_posts: Use this tool to get the useful old posts for a business which can be repurposed.
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
The task is to repurpose an old post which performed well. To accomplish this task, we will need to get the old useful posts.
Once we have the posts available, repurpose the most appropriate posts based on the below instructions.

Note: If by chance, we do not have any posts to repurpose then the final output will be empty with it being marked as error.

Rephrasing Instructions:
1. Rephrase the post based on the given content. 
2. Ensure the rephrased post is of similar length to the original post. 
3. Avoid fabricating information. 
4. Include the business name token wherever relevant. 
5. Do not include the parts with offers(e.g., 30% off, starting at just $$), season-specific content, time-specific content or reference any individual. Focus only on the parts which does not fall into these categories. Like, information about services or products, or some engaging content, etc.
6. Cross-verify that the rephrased post information matches the information given in the original post. If the information does not match, rephrase the post with the correct information. 
'''

classification_prompt = '''
We are given a social media post. The platform can be anything. Your task is to analyse the given post and 
decide if it can be used later on as a template to generate another post. 
For your analysis, you do not have any other metric except for the content of the post. 

The useful posts will be fed into a generation model to be repurposed as a new post later on.
<Categories>\nuseful\nuseless\n</Categories>\n
<What is a useless post>\n- offers\n- time specific\n-day specific\n- season specific\n- holiday
- employee announcement (new hires, promotions, anniversaries, retirements)\n- company anniversary
- person or some entity specific\n- event specific\n- feedback\n- new office\n- sponsorship
- wishes (festivals, special day wishes, etc.)\n- test (including meaningless posts)
- not useful, where you cannot think of any reason where this post should be saved to repurpose.

<What is Useful>
Any post which can be used later on as a template for a new post should be marked as useful. 
A useful post should have enough content in it to be repurposed later.
A useful post can be a random post (with no information or business context) whose job is just to engage the customers.

In case that you are not able to decide, mark the post as useful.

Below is the post to be classified:
{post}

Output Format:
The output should strictly be only <useful> or <useless>. Use <failure> tag in case of any issues.
'''

# The post being fed has high engagement and, the low engagement posts are being ignored completely, so you can ignore this and just focus on the content.
default_user_prompt = '''
Keep the above system instructions in mind. 
Below are some special instructions requested by the user, separated by new line. 
If any conflicting instructions occur, prioritise the system instructions. 
If you cannot follow some instructions, then ignore that and inside <error_message> you can output why you couldn't follow some instruction if any.
Below might also be some values which may or may not be useful for tool calling.\n
'''

competitor_system_prompt = '''
You are a social media content writer/post creator. Your task is to create social media posts for a business using the content from competitors' posts.
### Objectives:
To create proper posts which drives value to the business and its customers.
To strictly follow the instructions given mentioned below and give preferences to the user instructions if any.
To ensure config is followed strictly in priority order and consistently perform the analysis.
### Instructions:
Step 1. Create {count} social media posts using content from competitors for the given business.
Step 2. Check the tool catalog for the definition and use the appropriate tool to fetch the data. Business name and tools to invoke.
Tools: {tools_list} 
```Business Name: {business_name}, Based on {config} if evaluation_metric is 'Engagement' means `engagement` is 1 else 0 and `duration` (in days).
Step 3. Use the config {config} for each tool on specific constraints strictly for further analysis. 
Step 4. From Step 3. the fetched posts, evaluate and classify each post using the following rules:
<useful> - if the post content is reusable or adaptable for future business posts.
<useless> -  if it is highly specific (e.g., direct promotions, personal wishes, staff announcements).
<failure> -  if the post content is missing or unreadable.
Only proceed with posts marked as <useful> for further content generation tailored to the business {business_name}.
If no posts are marked as <useful>, analyse again and pick atleast 1 best to proceed further, pick leniently. 
Step 5. Before generating the posts, provide intermediate steps of what all data you are fetching after above steps before you generate posts.
should include tool name, number of posts in a tool, published date, evaluation metric only.
<!-- Follow step 3 strictly to filter the posts. -->
<filtered_posts_tool_level_list>
Tool Name: Tool name from where posts are fetched
Published Date: Published date of the posts in readable time format (filtered based on config `duration`.)
Evaluation Metric: Evaluation metric for posts (to verify with evaluation metric in config)
Total Posts: Number of posts fetched from the tool (to verify with num_posts in config)
</filtered_posts_tool_level_list
used for analysis. This is just for intermediate step to verify filtered data is inline with config.
Step 6. After analysis, generate the posts using the filtered data and output strictly in the below format {format_instructions_list} if no posts are available, just return empty list in the final output format.
'''


currentDate = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

class GetPostInputSchema(BaseModel):
    channels: List[Literal['facebook', 'twitter', 'instagram']] = Field(
        default= ['facebook', 'twitter', 'instagram'],
        description="The channel or platform for which we need to get the posts. By default set it to all available channels"
    )
    accountId: int = Field(
        description='The Enterprise ID'
    )
    pageSize: Optional[int] = Field(
        default=10,
        description='The number of posts to get from the system'
    )
    startDate: str = Field(
        description="Start Date of the date range specified. This should be in this format always, yyyy-MM-dd HH:mm:ss"
    )
    endDate: str = Field(
        default=currentDate,
        description="End Date of the date range specified. This should be in this format always, yyyy-MM-dd HH:mm:ss"
    )

class SingleGetPostOutputSchema(BaseModel):
    post: str = Field(
        description="The Old Post"
    )
    channel: Literal["facebook", "twitter", "instagram"] = Field(
        description="The channel or platform on which the post was posted"
    )

class GetPostOutputSchema(BaseModel):
    posts: List[SingleGetPostOutputSchema] = Field(
        description="List of posts along with their channels or platforms"
    )

@tool("get_useful_posts", args_schema=GetPostInputSchema)
def get_useful_posts(channels, accountId, startDate, endDate=currentDate, pageSize=10):
    """Gets the old useful posts which can be repurposed along with their channel"""
    posts = []
    llm = init_chat_model(
        "anthropic:claude-3-5-sonnet-latest",
        model_kwargs={"anthropic_api_key": os.getenv('ANTHROPIC_KEY')}
    )

    for channel in channels:
        url = f"http://socialapi.birdeye.com/social/insights/es/{channel}/post?sortParam=posted_date&startIndex=0&sortOrder=DESC&pageSize={pageSize}"

        payload = json.dumps({
            "businessIds": businessIds.get(accountId, []),
            "startDate": startDate,
            "endDate": endDate,
            "reportType": "POST_INSIGHT",
            "enterpriseId": 149546071353527,
            "tagIds": []
        })

        headers = {
            'SERVICE-NAME': 'AMBASSADOR',
            'user-id': '2230165',
            'account-id': str(accountId),
            'Content-Type': 'application/json'
        }
        response = requests.request("PUT", url, headers=headers, data=payload)
        temp = json.loads(response.text).get('pagePostData', [])
        for x in temp:
            post = x['postContent']
            if post:
                if not is_useless_post(post):
                    response = llm.invoke([
                        SystemMessage(content=''),  # Use SystemMessage
                        HumanMessage(content=classification_prompt.format(post=post))
                    ])
                    if '<useful>' in response.text():
                        posts.append({'post':post, 'channel':channel})

    print(posts)
    return posts


def is_useless_post(post_text):
    # Rule 0: length check
    if len(str(post_text)) < 50:
        return True

    # Rule 1: Check for time-sensitive keywords
    time_sensitive_keywords = [
        "today", "tomorrow", "yesterday", "this week", "next week", "last week", "annual",
        "this month", "next month", "last month", "deadline", "expires", "limited time", "sale ends", "register now"
    ]  # "join us", "adopt", "rehome", "rehoming", "adoption","found", "lost", "missing", "event", "raffle", "winner",
    if any(keyword in post_text.lower() for keyword in time_sensitive_keywords):
        return True

    # Rule 2: Check for dates (e.g., "2024-12-25", "December 25", "12/25/2024")
    date_patterns = [
        r"\b\d{4}-\d{2}-\d{2}\b",  # YYYY-MM-DD
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",  # MM/DD/YYYY or MM/DD/YY
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{1,2}(?:st|nd|rd|th)?,\s\d{4}\b"
        # Month Day, Year
    ]
    for pattern in date_patterns:
        if re.search(pattern, post_text):
            return True

    # # Rule 3: Check for specific case references (e.g., "Polly’s severe mastitis treatment")
    # case_reference_keywords = [
    #     "case", "treatment", "surgery", "recovery", "diagnosis", "emergency",
    #     "procedure", "injury", "accident"
    # ] # "found dog", "lost cat", "missing pet"
    # if any(keyword in post_text.lower() for keyword in case_reference_keywords):
    #     return True

    # Rule 4: Check for one-time achievements or announcements
    one_time_keywords = [
        "winner", "award", "recognition", "achievement", "congratulations",
        "special thanks", "shoutout", "announcement"
    ]  # "thank you"
    if any(keyword in post_text.lower() for keyword in one_time_keywords):
        return True

    # Rule 5: Check for expired promotions or events
    expired_keywords = [
        "sale", "discount", "promotion"

    ]  # "raffle", "event", "open house", "parade", "festival", "celebration", "fundraiser", "offer"
    if any(keyword in post_text.lower() for keyword in expired_keywords):
        return True

    # Rule 6: Check for seasonal or holiday-related content
    seasonal_keywords = [
        "Christmas", "New Year", "Easter", "Halloween", "Thanksgiving",
        "Valentine's Day", "Independence Day", "Labor Day", "Memorial Day",
        "holiday", "seasonal", "winter", "spring", "summer", "autumn"
    ]  # "fall"
    if any(keyword in post_text.lower() for keyword in seasonal_keywords):
        return True

    # Rule 10: Check for urgency indicators
    urgency_keywords = [
        "last chance", "don’t miss out", "act now", "limited slots", "final day"
    ]
    if any(keyword in post_text.lower() for keyword in urgency_keywords):
        return True

    # If none of the rules match, the post is considered reusable
    return False

businessIds = {1148914: [1159063,1159067,1181902,1181903,1181904,1181905,1181906,1181907,1181908,1181909,1181910,
                         1181911,1181912,1181913,1181914,1181915,1181916,1181917,1181918,1181919,1181920,1181921,
                         1181922,1181923,1181924,1181925,1181926,1181927,1181928,1182462,1182463,1210155,1210156,
                         1225244,1225245,1229151,1229152,1229153,1229154,1314340,1541748],
               1230007: [1230008,1234600,1234601,1234602,1234603,1234604,1234622,1234623,1234624,1234625,1234626,1234627,1234628,1234629,1234630,1234631,1234632,1234633,1234634,1234635,1234636,1234637,1234638,1234639,1234640,1234641,1234642,1234643,1234644,1234645,1234646,1234647,1234648,1234649,1234650,1234651,1234652,1234653,1234654,1234655,1234656,1234657,1234658,1234659,1234660,1234661,1234662,1234663,1234664,1234665,1234666,1234667,1234668,1234669,1234670,1234671,1234672,1234673,1234674,1234675,1234676,1234677,1234678,1234679,1234680,1234681,1234682,1234683,1234684,1234685,1234686,1234687,1234688,1234689,1234690,1234691,1234692,1234693,1234694,1234695,1234696,1234697,1234698,1234699,1234700,1234701,1234702,1234703,1234704,1234705,1234706,1234707,1234708,1234709,1234710,1234711,1234712,1234713,1234714,1234715,1234716,1234717,1234718,1234719,1234720,1234722,1264924],
               1264350: [1276093,1276241,1276242,1276243,1276244,1276245,1276246,1276247,1276248,1276249,1276250,1302236,1302237,1302238,1302239,1302240,1302241,1302242,1302243,1302244,1302245,1302246,1302247,1302248,1302249,1302250,1302251,1302252,1302253,1302254,1302255,1302256,1302257,1302258,1302259,1302260,1302261,1302262,1302263,1302264,1302265,1302266,1302267,1302268,1302269,1302270,1302271,1302272,1302273,1302274,1302275,1302276,1302277,1302278,1302279,1302280,1302281,1302282,1302283,1302284,1302285,1302286,1302287,1302288,1302289,1302290,1302291,1302292,1302293,1302294,1302295,1302296,1302297,1302298,1302299,1302300,1302301,1302302,1302303,1302304,1302305,1302306,1302307,1302308,1302309,1302310,1302311,1302313,1302314,1302315,1302316,1302317,1302318,1302319,1302320,1302321,1302322,1302323,1302324,1302325,1302326,1302327,1302328,1302329,1302330,1302331,1302332,1302333,1302334,1302335,1302336,1302337,1302338,1302339,1302340,1302341,1302342,1302343,1302344,1302345,1302346,1302347,1302348,1302349,1302350,1302351,1302352,1302353,1302354,1302355,1302356,1304487,1312185,1333277,1342640,1342641,1345774,1373460,1373461,1373462,1373914,1453562,1453566,1453568,1492966,1492968,1492969,1492970,1493737,1507969,1531412,1531413,1534274],
               26164: [1230008,1234600,1234601,1234602,1234603,1234604,1234622,1234623,1234624,1234625,1234626,1234627,1234628,1234629,1234630,1234631,1234632,1234633,1234634,1234635,1234636,1234637,1234638,1234639,1234640,1234641,1234642,1234643,1234644,1234645,1234646,1234647,1234648,1234649,1234650,1234651,1234652,1234653,1234654,1234655,1234656,1234657,1234658,1234659,1234660,1234661,1234662,1234663,1234664,1234665,1234666,1234667,1234668,1234669,1234670,1234671,1234672,1234673,1234674,1234675,1234676,1234677,1234678,1234679,1234680,1234681,1234682,1234683,1234684,1234685,1234686,1234687,1234688,1234689,1234690,1234691,1234692,1234693,1234694,1234695,1234696,1234697,1234698,1234699,1234700,1234701,1234702,1234703,1234704,1234705,1234706,1234707,1234708,1234709,1234710,1234711,1234712,1234713,1234714,1234715,1234716,1234717,1234718,1234719,1234720,1234722,1264924]
               }

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
def fetch_business_competitors_facebook(business_name: str,duration: int,engagement: int) -> Dict[str, Any]:
    """Fetches competitors data for a given business name and channel 'Facebook'
     duration - from current date and publishedDate should be within the given duration.
    engagement - should be greater than the given engagement.
    """
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_epoch_millis = int(today_start.timestamp() * 1000)
    with open("competitors_mock.json", "r") as f:
        competitors_data = json.load(f)
        if business_name in competitors_data:
            posts = competitors_data.get(business_name, {}).get("postData", [])
            results = [
    post for post in posts
    if (
        post.get("channel") == "facebook"
        and (today_epoch_millis - post.get("publishedDate", 0)) <= (duration *24 * 60 * 60 * 1000)
    )
]
            return f"Below is the competitors data {results}"
    return "No Data Found"
@tool
def fetch_business_competitors_instagram(business_name: str,duration: int,engagement: int) -> Dict[str, Any]:
    """Fetches competitors data for a given business name  and channel 'Instagram',
      duration - from current date and publishedDate should be within the given duration.
    engagement - should be greater than the given engagement.
    """
    results = []
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_epoch_millis = int(today_start.timestamp() * 1000)
    with open("competitors_mock.json", "r") as f:
        competitors_data = json.load(f)
        if business_name in competitors_data:
            posts = competitors_data.get(business_name, {}).get("postData", [])
            results = [
    post for post in posts
    if (
        post.get("channel") == "instagram"
        and (today_epoch_millis - post.get("publishedDate", 0)) <= (duration *24 * 60 * 60 * 1000)
    )
]
        return f"Below is the competitors data {results}"
    return "No Data Found"

@tool
def fetch_business_competitors_twitter(business_name: str,duration: int,engagement: int) -> Dict[str, Any]:
    """Fetches competitors data for a given business name  and platform 'Twitter'
    duration - from current date and publishedDate should be within the given duration.
    engagement - should be greater than the given engagement.
    """
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_epoch_millis = int(today_start.timestamp() * 1000)
    with open("competitors_mock.json", "r") as f:
        competitors_data = json.load(f)
        if business_name in competitors_data:
            posts = competitors_data.get(business_name, {}).get("postData", [])
            results = [
    post for post in posts
    if (
        post.get("channel") == "twitter"
        and (today_epoch_millis - post.get("publishedDate", 0)) <= (duration *24 * 60 * 60 * 1000)
    )
]
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