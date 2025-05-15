from typing import List, TypedDict, Annotated, Optional
import operator, math
from dotenv import load_dotenv
import json
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from pydantic import BaseModel, Field

from default_values import *

load_dotenv()

class MessagesState(TypedDict):
    # input payload
    total_post: int
    number_of_days: int
    small_id: str
    long_id: str
    business_name: str
    categories: List[str]
    prompt_config: dict

    # API fills
    holidays: List[dict]
    business_info: str
    business_category: str

    # Agent/code fills
    holiday_post_count: int
    business_post_count: int
    repurpose_post_count: int
    competitor_post_count: int
    trends_post_count: int

    holiday_outputs: Annotated[List[dict], operator.add]
    business_outputs: Annotated[List[dict], operator.add]
    repurpose_outputs: Annotated[List[dict], operator.add]
    competitor_outputs: Annotated[List[str],operator.add]
    trending_outputs: Annotated[List[str],operator.add]

    combined_posts: Annotated[List[dict], operator.add]


class PostContent(BaseModel):
    post: str = Field(description="Main content of the post")
    keywords: str = Field(description="image caption to search on pixel/pexabay which can be used in the post")

class PostList(BaseModel):
    posts: List[PostContent]

class HolidayOutput(BaseModel):
    post: str = Field(description="The holiday post generated")
    keywords: str = Field(description="Keywords for the holiday post")
    event: str = Field(description="The event on which the post is based")
    error_message: Optional[str] = Field(description="Optional error message if there was an issue", default=None)

class BusinessOutput(BaseModel):
    post: str = Field(description="The business post generated")
    keywords: str = Field(description="Keywords for the business post")
    idea: str = Field(description="Idea on which the post is generated")
    error_message: Optional[str] = Field(description="Optional error message if there was an issue", default=None)

class RepurposeOutput(BaseModel):
    post: str = Field(description="The repurposed content post generated")
    keywords: str = Field(description="Keywords for the repurposed content post")
    # original_post: str = Field(description)
    error_message: Optional[str] = Field(description="Optional error message if there was an issue", default=None)

output_parser = JsonOutputParser(pydantic_object=PostContent)
format_instructions = output_parser.get_format_instructions()

output_parser_list = PydanticOutputParser(pydantic_object=PostList)
format_instructions_list = output_parser_list.get_format_instructions()

class SocialMediaPostGenerator:
    def __init__(self):
        self.llm_holiday = ChatOpenAI(model="gpt-4o")
        self.llm_business = ChatOpenAI(model="gpt-4o")
        self.llm_repurpose = ChatOpenAI(model="gpt-4o")
        self.llm_competitor = ChatOpenAI(model="gpt-4o")
        self.llm_trending = ChatOpenAI(model="gpt-4o")
        self.graph = self._build_graph()


    def _get_repurpose_topics(self, n: int) -> List[str]:
        return [f"Repurpose Topic {i + 1}" for i in range(n)]

    def _get_image_for_post(self, content: str) -> str:
        return search_pixabay_images(content)

    # ---- Node Functions ----
    def allocate_source_count(self, state: MessagesState) -> MessagesState:
        total = state["total_post"]
        categories = state["categories"]
        holiday_count = state['holiday_post_count']

        repurpose_post, business_post, competitor_post, trending_post = 0, 0, 0, 0
        remaining = total - holiday_count

        if PostType.REPURPOSED_POST.name in categories:
            repurpose_post = 1

        if PostType.BUSINESS_IDEAS_POST.name in categories:
            business_post = 1

        if PostType.COMP.name in categories:
            competitor_post = 1

        if PostType.TRENDING.name in categories:
            trending_post = 1

        total_sources = repurpose_post + business_post + competitor_post + trending_post

        if total_sources > remaining:
            if total_sources - remaining == 1:
                business_post = 0
            elif total_sources - remaining == 2:
                business_post = 0
                trending_post = 0
            elif total_sources - remaining == 3:
                business_post = 0
                trending_post = 0
                competitor_post = 0
            else:
                business_post = 0
                trending_post = 0
                competitor_post = 0
                repurpose_post = 0
        # total_sources = repurpose_post + business_post + competitor_post + trending_post
            # business_post += remaining - total_sources
        # else:
        repurpose_post *= round(remaining/total_sources)
        remaining -= repurpose_post

        competitor_post *= round(remaining/(total_sources-1))
        remaining -= competitor_post

        trending_post *= round(remaining/(total_sources-2))
        remaining -= trending_post

        # business_post *= math.floor(remaining/total_sources)

        business_post = remaining

        updates = {
            "business_post_count": business_post,
            "repurpose_post_count": repurpose_post,
            "competitor_post_count": competitor_post,
            "trends_post_count": trending_post,
            "trending_outputs": []
        }

        return updates


    def holiday_agent(self, state: MessagesState) -> dict:
        total = state["total_post"]
        categories = state["categories"]

        # BE APIs
        holidays = get_upcoming_week_holidays(state['number_of_days'])
        category, business_info = get_business_meta(state['small_id'])

        if PostType.HOLIDAY_POST.name in categories and holidays and total > 0:
            pass
        else:
            # error = HolidayOutput(post='',
            #                       keywords='',
            #                       event='',
            #                       error_message='Validation Failure while generating Holiday Posts').model_dump()
            # error['source'] = 'HOLIDAY_POST'

            return {"holiday_outputs": [], # error
                    "holiday_post_count": 0,
                    "holidays": holidays,
                    "business_category": category,
                    "business_info": json.dumps(business_info)}

        holiday_count = len(holidays)
        user_prompts = "\n".join(state["prompt_config"].get("HOLIDAY_POST", []))
        results = []
        parser = JsonOutputParser(pydantic_object=HolidayOutput)

        for holiday in holidays:
            if user_prompts:
                user_prompts = "Keep the above instructions in mind. Below are some special instructions requested by the user, separated by new line. If any conflicting instructions occur, prioritise the above instructions. If you cannot follow some instructions, then ignore that and inside <error_message> you can output why you couldn't follow some instruction if any.\n\n" + user_prompts

            format_instructions_local = parser.get_format_instructions()
            system_content = (
                f"{holiday_system_prompt.format(holiday=holiday['holiday'], businessDetails=business_info)}\n\n"
                f"{keyword_generator_system}"
                f"Return your response as JSON according to these instructions:\n{format_instructions_local}"
            )

            sys_msg = SystemMessage(content=system_content)
            raw_result = self.llm_holiday.invoke([sys_msg, HumanMessage(content=user_prompts)])

            try:
                # Parse the JSON result directly
                parsed_result = parser.parse(raw_result.content)
                parsed_result['source'] = 'HOLIDAY'
                results.append(parsed_result)
            except Exception as e:
                # If parsing fails, create a fallback response
                error_msg = HolidayOutput(
                    post="",
                    keywords="",
                    error_message=f"Error parsing output: {str(e)}"
                )
                results.append(error_msg.model_dump())

        return {"holiday_outputs": results,
                "holiday_post_count": holiday_count,
                "holidays": holidays,
                "business_category": category,
                "business_info": json.dumps(business_info)}


    def get_trends_agent(self, state: MessagesState) -> dict:
        """
        Retrieves latest trending topics for a given business.
        """
        count = state['trends_post_count']
        if count == 0:
            return {"trending_outputs": []}

        results = []
        trends_data = fetch_business_competitors_trends(1)
        business_name = state['business_category']
        user_prompts = "\n".join(state["prompt_config"].get("TRENDING", []))
        if business_name in trends_data:
            prompt = f"Create a social media posts using content from latest trends for the given business:. \
            \ Include context for a the business. {format_instructions}"
            if user_prompts:
                prompt = prompt + f"\nBelow are the instructions given by end user for customisation, take those into consideration if it conflicts, strict to the main instructions \
                User instructions:{user_prompts}"""
            sys_msg = SystemMessage(content="You are a helpful assistant for generating posts according to trends.")
            result = self.llm_trending.invoke([sys_msg, HumanMessage(content=prompt)])
            parsed_result = output_parser.parse(result.content)
            parsed_result['source'] = "TRENDS"
            results.append(parsed_result)
            print("Trends")
            return {"trending_outputs": results}
        else:
            return {"error": f"No trends data found for business: {business_name}"}


    def get_competitor_agent(self, state: MessagesState) -> dict:
        """
        Retrieves competitor posts (company-specific events, testimonials, seasonal offers) for a given business.
        """
        count = state['competitor_post_count']
        results = []
        if count == 0:
            return {"competitor_outputs": []}
        competitors_data = fetch_business_competitors_trends(0)
        business_name = state['business_name']
        user_prompts = "\n".join(state["prompt_config"].get("COMP", []))
        if business_name in competitors_data:
            prompt = f"Create a social media posts using content from competitors for the given business: {competitors_data}.Ignore the categories like company specific events. \
            \ Include context for a dental business. {format_instructions}"
            if user_prompts:
                prompt = prompt + f"\nBelow are the instructions given by end user for customisation, take those into consideration if it conflicts, strict to the main instructions \
                User instructions:{user_prompts}"""
            sys_msg = SystemMessage(
                content="You are a helpful assistant for generating posts similar to competitors posts.")
            result = self.llm_competitor.invoke([sys_msg, HumanMessage(content=prompt)])
            parsed_result = output_parser.parse(result.content)
            parsed_result['source'] = "COMPETITORS"
            results.append(parsed_result)
            return {"competitor_outputs": results}
        else:
            return {"error": f"No competitor data found for business: {business_name}"}


    def business_agent(self, state: MessagesState) -> dict:
        # count = state["business_post_count"]
        holiday_count = len(state['holiday_outputs'])
        repurpose_count = len(state['repurpose_outputs'])
        competitor_count = len(state['competitor_outputs'])
        trend_count = len(state['trending_outputs'])

        total = state['total_post']

        remaining = total - (holiday_count + repurpose_count + competitor_count + trend_count)
        count = remaining

        business_info = state["business_info"]
        user_prompts = "\n".join(state["prompt_config"].get("BUSINESS_IDEAS_POST", []))
        results = []

        # Define a specialized model for batch output
        class BusinessBatchOutput(BaseModel):
            posts: List[dict] = Field(description="List of business posts with 'post', 'idea' and 'keywords' fields")
            # ideas: List
            error_message: Optional[str] = Field(description="Optional error message if there was an issue",
                                                 default=None)

        batch_parser = JsonOutputParser(pydantic_object=BusinessBatchOutput)

        for i in range(0, count, 5):
            batch_size = min(5, count - i)


            if user_prompts:
                user_prompts = "\n\nKeep the above instructions in mind. Below are some special instructions requested by the user, separated by new line. If any conflicting instructions occur, prioritise the above instructions. If you cannot follow some instructions, then ignore that and inside <error_message> you can output why you couldn't follow some instruction if any.\n\n" + user_prompts

            format_instructions_local = batch_parser.get_format_instructions()

            system_content = (
                f"{business_idea_system.format(num=batch_size, business_details=business_info)}\n\n"
                f"{keyword_generator_system}"
                f"Return your response as JSON according to these instructions:\n{format_instructions_local}"
            )

            sys_msg = SystemMessage(content=system_content)
            print(" System Message: ------------- ---- ", sys_msg.content)
            print(" User Prompts: ------------- ---- ", user_prompts)
            raw_result = self.llm_business.invoke([sys_msg, HumanMessage(content=user_prompts)])

            try:
                # Parse the batch JSON result
                parsed_batch = batch_parser.parse(raw_result.content)
                for i in parsed_batch['posts']:
                    i['source'] = 'BUSINESS_IDEA'

                # Add each post from the batch to results
                results.extend(parsed_batch["posts"])
            except Exception as e:
                # If parsing fails, create fallback responses for the batch
                for j in range(batch_size):
                    error_msg = BusinessOutput(
                        post="",
                        keywords="",
                        error_message=f"Error parsing batch output: {str(e)}"
                    )
                    results.append(error_msg.dict())

        return {"business_outputs": results,
                "business_post_count": count}


    def repurpose_agent(self, state: MessagesState) -> dict:
        count = state["repurpose_post_count"]
        enterpriseId = state['long_id']
        if count == 0:
            return {"repurpose_outputs": []}

        # repurpose_topics = self._get_repurpose_topics(count)
        own_top_perfroming_posts = get_repurposed_posts(enterpriseId, count)

        user_prompts = "\n".join(state["prompt_config"].get("REPURPOSED_POST", []))
        results = []
        parser = JsonOutputParser(pydantic_object=RepurposeOutput)

        for post in own_top_perfroming_posts:
            topic_prompt = f"Create a social media post using the old post."

            if user_prompts:
                topic_prompt = topic_prompt + default_user_prompt + user_prompts

            format_instructions_local = parser.get_format_instructions()
            system_content = (
                f"{repurposed_post_system.format(post=post['postText'])}"
                f"{keyword_generator_system}"
                f"Return your response as JSON according to these instructions:\n{format_instructions_local}"
            )

            sys_msg = SystemMessage(content=system_content)
            print(" R System Message: ------------- ---- ", sys_msg.content)
            print(" R User Prompts: ------------- ---- ", topic_prompt)   
            raw_result = self.llm_repurpose.invoke([sys_msg, HumanMessage(content=topic_prompt)])

            try:
                # Parse the JSON result directly
                parsed_result = parser.parse(raw_result.content)
                parsed_result['source'] = 'REPURPOSED'

                results.append(parsed_result)
            except Exception as e:
                # If parsing fails, create a fallback response
                error_msg = RepurposeOutput(
                    post="",
                    keywords="",
                    # topic=topic,
                    error_message=f"Error parsing output: {str(e)}"
                )
                results.append(error_msg.model_dump())

        return {"repurpose_outputs": results}

    def combine_posts(self, state: MessagesState) -> dict:
        all_posts = state["holiday_outputs"] + state["business_outputs"] + state["repurpose_outputs"] + state[
            'competitor_outputs']
        enriched = [{"content": post, 'source': post['source'], "image_url": self._get_image_for_post(post['keywords'])} for post in all_posts]
        return {"combined_posts": enriched}

    def fetch_n_btp(self, state: MessagesState):
        total_posts = state['combined_posts']
        n_posts = len(total_posts)

        time_slots = fetch_btp()
        slots = get_best_time_slots_next_7_days(time_slots['timeSlots'], n_posts)
        for post, slot in zip(total_posts, slots):
            post['slot'] = slot

        return {'combined_posts': total_posts}

    def _build_graph(self):
        builder = StateGraph(MessagesState)

        builder.add_node("holiday_agent", self.holiday_agent)
        builder.set_entry_point("holiday_agent")

        builder.add_node("allocate_source_count", self.allocate_source_count)
        builder.add_edge("holiday_agent", "allocate_source_count")

        builder.add_node("repurpose_agent", self.repurpose_agent)
        builder.add_node("competitor_agent", self.get_competitor_agent)
        builder.add_node("trends_agent", self.get_trends_agent)

        builder.add_edge("allocate_source_count", "repurpose_agent")
        builder.add_edge("allocate_source_count", "competitor_agent")
        builder.add_edge("allocate_source_count", "trends_agent")

        builder.add_node("business_agent", self.business_agent)
        builder.add_edge("repurpose_agent", "business_agent")
        builder.add_edge("competitor_agent", "business_agent")
        builder.add_edge("trends_agent", "business_agent")

        builder.add_node("combine_posts_and_add_image", self.combine_posts)
        builder.add_edge("business_agent", "combine_posts_and_add_image")
        # builder.add_node("Analyse & Select Best Time to Post", self.fetch_n_btp)

        builder.add_edge("combine_posts_and_add_image", END)
        # builder.add_edge('Analyse & Select Best Time to Post', END)

        return builder.compile()

    def generate(self, input_payload: dict) -> dict:
        return self.graph.invoke(input_payload)


input_payload = {
    "total_post": 6,
    'small_id': '1148914',
    'long_id': '169030216166956',
    'business_name': 'Village Pet Care',
    'number_of_days': 10,
    # "business_info": "We provide expert dental care and cleaning services with cutting-edge equipment and experienced staff.",
    # "business_name": "Aspen Dental",
    # "business_category":"dental_us",
    "categories": ["HOLIDAY_POST", "BUSINESS_IDEAS_POST", "REPURPOSED_POST", "TRENDING", "COMP"],
    "prompt_config" : {"holiday" : []}
}
# 'make diwali post very bright. use colorful emojis', 'st. patricks post should alcohol focused. Connect it to some dental health concern.'


# social_agent = SocialMediaPostGenerator()
#
# posts = social_agent.generate(input_payload)
#
# for post in posts["combined_posts"]:
#     print(f"Source:{post['source']}\nContent:\n{post['content']}\nImage: {post['image_url']}\n{'-'*50}")
#
