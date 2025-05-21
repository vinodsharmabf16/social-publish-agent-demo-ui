import concurrent.futures
from typing import List, TypedDict, Annotated, Optional
import operator, math
from dotenv import load_dotenv
import json

from langchain.agents import initialize_agent, AgentType, create_openai_functions_agent, AgentExecutor, \
    OpenAIFunctionsAgent
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from default_values import *

load_dotenv(override=True)

class MessagesState(TypedDict):
    # input payload
    total_post: int
    number_of_days: int
    small_id: str
    long_id: str
    business_name: str
    categories: List[str]
    prompt_config: dict
    active_tools: List[str]
    tools: dict

    # API fills
    holidays: List[dict]
    business_info: str
    business_category: str

    # Agent/code fills
    last_call: Annotated[List[BaseMessage], operator.add]
    holiday_post_count: int
    business_post_count: int
    repurpose_post_count: int
    competitor_post_count: int
    trending_post_count: int

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
    posts: List[PostContent] = Field(description="List of posts with 'post' and 'keywords' fields , if no posts generated, return empty list")

class HolidayOutput(BaseModel):
    post: str = Field(description="The post generated")
    # keywords: str = Field(description="Image caption to search on pexel/pixabay which can be used in the post")
    event: str = Field(description="The name of the holiday or event on which the post is generated")
    error_message: Optional[str] = Field(description="Optional error message if there was an issue", default=None)

class HolidayBatch(BaseModel):
    posts: Optional[List[HolidayOutput]]
    business_category: str = Field(description="The business main category if available. If not return empty string")
    business_info: dict = Field(description="The rest of the business info apart from the category, in a dictionary format. If not, return empty dictionary")
    error: bool = Field(description="Should be true if no available holiday and no post is generated. Else, False")

class BusinessOutput(BaseModel):
    post: str = Field(description="The business post generated")
    # keywords: str = Field(description="Image caption to search on pexel/pixabay which can be used in the post")
    idea: str = Field(description="Idea on which the post is generated")
    error_message: Optional[str] = Field(description="Optional error message if there was an issue", default=None)

# Define a specialized model for batch output
class BusinessBatchOutput(BaseModel):
    posts: List[BusinessOutput] = Field(description="List of objects with three string fields 'post', 'idea' and 'keywords'")
    # ideas: List
    error_message: Optional[str] = Field(description="Optional error message if there was an issue",
                                         default=None)

class RepurposeOutput(BaseModel):
    post: str = Field(description="The repurposed content post generated")
    # keywords: str = Field(description="Image caption to search on pixel/pexabay which can be used in the post")
    # original_post: str = Field(description)
    error_message: Optional[str] = Field(description="Optional error message if there was an issue", default=None)

class RepurposeBatch(BaseModel):
    posts: Optional[List[RepurposeOutput]]
    error: bool = Field(description="Should be true if couldn't find any old post to repurpose on or no post is generated. Else, False")

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
        self.tools = [tool_get_upcoming_week_holidays, tool_get_business_meta]

        self.graph = self._build_graph()
        self._build_graph_image()

    def _get_repurpose_topics(self, n: int) -> List[str]:
        return [f"Repurpose Topic {i + 1}" for i in range(n)]

    def _get_image_for_post(self, content: str):
        if content:
            return search_pixabay_images(content)
        return []

    def _build_graph(self):
        builder = StateGraph(MessagesState)
        # tool_executor_node = ToolNode(self.tools)

        builder.add_node("Agent_Holiday", self.holiday_agent_tool)
        # builder.add_node("tools_node", tool_executor_node)

        builder.add_node("Function_Distribute_Sources", self.allocate_source_count)
        builder.add_node("Agent_RepurposeOldPosts", self.repurpose_agent_tool)
        builder.add_node("Agent_Competitors", self.get_competitor_agent)
        builder.add_node("Agent_Trends", self.get_trends_agent)
        builder.add_node("Agent_PostIdeas", self.business_agent)
        builder.add_node("Function_Combine_Posts+Recommend_Images", self.combine_posts)
        # builder.add_node("Analyse & Select Best Time to Post", self.fetch_n_btp)

        builder.set_entry_point("Agent_Holiday")

        # builder.add_conditional_edges(
        #     "holiday_agent", # Source node
        #     self.should_call_tool,  # Function to decide the route
        #     {
        #         "tools_node": "tools_node",   # If should_call_tool returns "tools", go to "tools" node
        #         "allocate_source_count": "allocate_source_count"      # If should_call_tool returns "__end__", go to END
        #     }
        # )

        builder.add_edge("Agent_Holiday", "Function_Distribute_Sources")

        builder.add_edge("Function_Distribute_Sources", "Agent_RepurposeOldPosts")
        builder.add_edge("Function_Distribute_Sources", "Agent_Competitors")
        builder.add_edge("Function_Distribute_Sources", "Agent_Trends")

        builder.add_edge("Agent_RepurposeOldPosts", "Agent_PostIdeas")
        builder.add_edge("Agent_Competitors", "Agent_PostIdeas")
        builder.add_edge("Agent_Trends", "Agent_PostIdeas")

        builder.add_edge("Agent_PostIdeas", "Function_Combine_Posts+Recommend_Images")

        builder.add_edge("Function_Combine_Posts+Recommend_Images", END)
        # builder.add_edge('Analyse & Select Best Time to Post', END)

        return builder.compile()

    def _build_graph_image(self):
        try:
            # Make sure your graph is compiled
            # graph = graph_builder.compile() # Already done earlier in your script

            # Option 1: Save as PNG (requires playwright)
            # Install with: pip install "langgraph[draw]" or pip install playwright; playwright install
            png_bytes = self.graph.get_graph().draw_mermaid_png()
            with open("SocialPublishingAgent.png", "wb") as f:
                f.write(png_bytes)
            print("Graph diagram saved as content_creator_graph.png")

            # Option 2: Get Mermaid syntax (if PNG generation fails or you prefer text)
            # mermaid_syntax = graph.get_graph().draw_mermaid()
            # print("\nMermaid Diagram Syntax (copy and paste into a Mermaid live editor):\n")
            # print(mermaid_syntax)

        except ImportError as e:
            print(f"ImportError: {e}. To generate PNGs, playwright is needed.")
            print("Install with: pip install \"langgraph[draw]\" or pip install playwright; playwright install")
            print("Alternatively, you can get the Mermaid syntax (uncomment that part in the code).")
        except Exception as e:
            print(f"An error occurred while generating the diagram: {e}")
            print("You can often visualize the graph execution in LangSmith if you have it configured.")

    # ---- Node Functions ----
    # def allocate_source_count(self, state: MessagesState) -> MessagesState:
    #     total = state["total_post"]
    #     categories = state["categories"]
    #     holiday_count = state['holiday_post_count']
    #
    #     repurpose_post, business_post, competitor_post, trending_post = 0, 0, 0, 0
    #     remaining = total - holiday_count
    #
    #     if PostType.REPURPOSED_POST.name in categories:
    #         repurpose_post = 1
    #
    #     if PostType.BUSINESS_IDEAS_POST.name in categories:
    #         business_post = 1
    #
    #     if PostType.COMP.name in categories:
    #         competitor_post = 1
    #
    #     if PostType.TRENDING.name in categories:
    #         trending_post = 1
    #
    #     total_sources = repurpose_post + business_post + competitor_post + trending_post
    #
    #     if total_sources > remaining:
    #         if total_sources - remaining == 1:
    #             business_post = 0
    #         elif total_sources - remaining == 2:
    #             business_post = 0
    #             trending_post = 0
    #         elif total_sources - remaining == 3:
    #             business_post = 0
    #             trending_post = 0
    #             competitor_post = 0
    #         else:
    #             business_post = 0
    #             trending_post = 0
    #             competitor_post = 0
    #             repurpose_post = 0
    #     # total_sources = repurpose_post + business_post + competitor_post + trending_post
    #         # business_post += remaining - total_sources
    #     # else:
    #
    #     if total_sources > 0:
    #         repurpose_post *= math.ceil(remaining / total_sources)
    #         remaining -= repurpose_post
    #
    #     if total_sources > 1:
    #         competitor_post *= math.ceil(remaining / (total_sources - 1))
    #         remaining -= competitor_post
    #
    #     if total_sources > 2:
    #         trending_post *= math.ceil(remaining / (total_sources - 2))
    #         remaining -= trending_post
    #
    #     # business_post *= math.floor(remaining/total_sources)
    #
    #     business_post = remaining
    #
    #     updates = {
    #         "business_post_count": business_post,
    #         "repurpose_post_count": repurpose_post,
    #         "competitor_post_count": competitor_post,
    #         "trending_post_count": trending_post,
    #         "trending_outputs": []
    #     }
    #
    #     return updates

    def allocate_source_count(self, state):
        total_post = state["total_post"]
        categories = state["categories"]
        holiday_count = state['holiday_post_count']

        # Initialize flags based on categories present
        repurpose_active = 1 if PostType.REPURPOSED_POST.name in categories else 0
        business_active = 1 if PostType.BUSINESS_IDEAS_POST.name in categories else 0
        competitor_active = 1 if PostType.COMP.name in categories else 0
        trending_active = 1 if PostType.TRENDING.name in categories else 0

        posts_available_for_sources = total_post - holiday_count
        if posts_available_for_sources < 0:
            posts_available_for_sources = 0

        # --- Reduction Logic (from original code's behavior) ---
        # Check how many categories are notionally active if each gets at least 1 post.
        # This part determines which flags (repurpose_active, etc.) might be turned off.
        # The original code initializes counts to 1 if active, then reduces.
        # We apply this to our flags.

        # Simulate initial "1 post per active category" to check against remaining posts
        _temp_repurpose = 1 if repurpose_active else 0
        _temp_business = 1 if business_active else 0
        _temp_competitor = 1 if competitor_active else 0
        _temp_trending = 1 if trending_active else 0

        current_total_active_sources_for_reduction = _temp_repurpose + _temp_business + _temp_competitor + _temp_trending

        if current_total_active_sources_for_reduction > posts_available_for_sources:
            diff = current_total_active_sources_for_reduction - posts_available_for_sources

            # This reduction priority (Business -> Trending -> Competitor -> Repurpose)
            # is derived from the original code's conditional `business_post = 0`, etc.
            if diff == 1:
                if business_active: business_active = 0
                # If business_active was already 0, the original code did not specify a fallback.
                # We will stick to this direct interpretation. If a more robust fallback is needed
                # (e.g., turn off trending if business is already off), that's a further change.
            elif diff == 2:
                if business_active: business_active = 0
                if trending_active: trending_active = 0
            elif diff == 3:
                if business_active: business_active = 0
                if trending_active: trending_active = 0
                if competitor_active: competitor_active = 0
            else:  # diff >= 4 (implies all were active and need to be turned off, or more than 4 sources)
                if business_active: business_active = 0
                if trending_active: trending_active = 0
                if competitor_active: competitor_active = 0
                if repurpose_active: repurpose_active = 0

        # --- End of Reduction Logic ---

        # Initialize post counts
        repurpose_post_count, business_post_count, competitor_post_count, trending_post_count = 0, 0, 0, 0

        current_remaining_posts = posts_available_for_sources

        # This is the `total_sources` from the original commented logic.
        # It's the number of categories that are *still active* after reduction.
        effective_total_active_sources = repurpose_active + competitor_active + trending_active + business_active

        if effective_total_active_sources > 0 and current_remaining_posts > 0:
            # --- Repurpose Post Allocation ---
            if repurpose_active:
                # Denominator for repurpose is all currently effective_total_active_sources
                denominator = effective_total_active_sources
                # This check for denominator > 0 is technically covered by `effective_total_active_sources > 0`
                # and `repurpose_active` being true, implying denominator >= 1.
                share = round(current_remaining_posts / denominator)
                count = min(max(0, int(share)), current_remaining_posts)  # Ensure non-negative and within available
                repurpose_post_count = count
                current_remaining_posts -= count

            # --- Competitor Post Allocation ---
            if competitor_active:
                # Denominator for competitor is effective_total_active_sources minus 1 if repurpose was active (and thus "took a slot")
                denominator = effective_total_active_sources - (1 if repurpose_active else 0)
                if denominator > 0:
                    share = round(current_remaining_posts / denominator)
                    count = min(max(0, int(share)), current_remaining_posts)
                    competitor_post_count = count
                    current_remaining_posts -= count
                elif current_remaining_posts > 0:  # Competitor active, but no denominator "slots" left (e.g., only C was active from start, or RP was active and C is next)
                    competitor_post_count = current_remaining_posts  # Gets all remaining if it's effectively the last one for sharing
                    current_remaining_posts = 0

            # --- Trending Post Allocation ---
            if trending_active:
                # Denominator for trending considers if repurpose and competitor were active
                denominator = effective_total_active_sources - (1 if repurpose_active else 0) - (
                    1 if competitor_active else 0)
                if denominator > 0:
                    share = round(current_remaining_posts / denominator)
                    count = min(max(0, int(share)), current_remaining_posts)
                    trending_post_count = count
                    current_remaining_posts -= count
                elif current_remaining_posts > 0:
                    trending_post_count = current_remaining_posts
                    current_remaining_posts = 0

        # --- Business Post Allocation (gets whatever is left, if active) ---
        if business_active:
            business_post_count = max(0, current_remaining_posts)  # Ensure non-negative
            current_remaining_posts -= business_post_count  # Should make current_remaining_posts zero

        # --- Handle Remainder (if business was not active and rounding left posts) ---
        # This distributes any posts left due to rounding if Business category was not active to absorb them.
        if current_remaining_posts > 0:
            # Create a list of R, C, T categories that are active, in order of priority
            eligible_for_remainder = []
            if repurpose_active: eligible_for_remainder.append("R")
            if competitor_active: eligible_for_remainder.append("C")
            if trending_active: eligible_for_remainder.append("T")

            idx = 0
            temp_rem = current_remaining_posts
            while temp_rem > 0 and len(eligible_for_remainder) > 0:
                category_to_increment = eligible_for_remainder[idx % len(eligible_for_remainder)]
                if category_to_increment == "R":
                    repurpose_post_count += 1
                elif category_to_increment == "C":
                    competitor_post_count += 1
                elif category_to_increment == "T":
                    trending_post_count += 1
                temp_rem -= 1
                idx += 1
            current_remaining_posts = temp_rem  # Should be 0 if distributed

        updates = {
            "business_post_count": business_post_count,
            "repurpose_post_count": repurpose_post_count,
            "competitor_post_count": competitor_post_count,
            "trending_post_count": trending_post_count,
        }
        print(updates)
        return updates

    # def should_call_tool(self, state: MessagesState) -> Literal["tools_node", "allocate_source_count"]:
    #     """
    #     Determines the next step based on the last message from the content_creator_agent.
    #     If the LLM made a tool call, route to the 'tool_executor_node'.
    #     Otherwise, the LLM has generated a direct response, so end the process.
    #     """
    #     print("--- Conditional Edge: should_call_tool ---")
    #     last_message = state["last_call"][-1]
    #
    #     if hasattr(last_message, "tool_calls") and last_message.tool_calls:
    #         print(f"Decision: Call tools {[(tc['name']) for tc in last_message.tool_calls]}")
    #         return "tools_node"
    #     print("Decision: End (no tool calls or direct response)")
    #     return "allocate_source_count"

    def holiday_agent_tool(self, state: MessagesState):
        total = state["total_post"]
        categories = state["categories"]
        businessId = state['small_id']
        num_days = total
        last_message = state["last_call"]
        tools = [tool_get_upcoming_week_holidays, tool_get_business_meta]

        if PostType.HOLIDAY_POST.name in categories and total > 0:
            pass
        else:
            # error = HolidayOutput(post='',
            #                       keywords='',
            #                       event='',
            #                       error_message='Validation Failure while generating Holiday Posts').model_dump()
            # error['source'] = 'HOLIDAY_POST'
            category, business_info = tool_get_business_meta(businessId)

            return {"holiday_outputs": [],
                    "holiday_post_count": 0,
                    "business_category": category,
                    "business_info": json.dumps(business_info)
                    }

        results = []
        parser = JsonOutputParser(pydantic_object=HolidayBatch)

        system_content = (f"{general_system_prompt}"
                        # f"{holiday_keyword_generator_system})"
                        f"{tools_prompt}"
                        f'''Return your response as JSON according to these instructions:\n{parser.get_format_instructions().replace("{", "{{").replace("}", "}}")}''')

        user_prompts = "\n".join(state["prompt_config"].get("HOLIDAY_POST", []))
        if user_prompts:
            user_prompts = default_user_prompt + user_prompts

        input_prompt = f'{user_prompts} \n BusinessId: {str(businessId)}\n Number of days: {num_days}\n'

        # Create the prompt template with system content
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_content),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        # Create the OpenAI Functions agent
        agent = create_openai_functions_agent(
            llm=self.llm_holiday,
            tools=tools,
            prompt=prompt
        )

        # Create the agent executor
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=tools,
            verbose=True
        )

        # Run the agent with just the input
        ai_response = agent_executor.invoke({"input": input_prompt})

        holiday_count = 0

        try:
            # Parse the JSON result directly
            parsed_result = parser.parse(ai_response['output'])
            if parsed_result['error']:
                print('No available Holidays. No Holiday posts generated.')
            else:
                for i in parsed_result['posts']:
                    i['source'] = 'HOLIDAY'
                    results.append(i)
                    holiday_count += 1

        except Exception as e:
            error_msg = HolidayOutput(
                post="",
                keywords="",
                error_message=f"Error parsing output: {str(e)}"
            )
            results.append(error_msg.model_dump())

        return {"holiday_outputs": results,
                "holiday_post_count": holiday_count,
                # "holidays": holidays,
                "business_category": parsed_result['business_category'],
                "business_info": json.dumps(parsed_result['business_info'])}
    
    # def holiday_agent(self, state: MessagesState) -> dict:
    #     total = state["total_post"]
    #     categories = state["categories"]
    #     active_tools = state["active_tools"]
    #     # tools = []
    #     # agent = initialize_agent(
    #     #     tools=tools,
    #     #     llm=self.llm_competitor,
    #     #     agent=AgentType.OPENAI_FUNCTIONS,
    #     #     verbose=True
    #     # )
    #     # BE APIs
    #     holidays = tool_get_upcoming_week_holidays(state['number_of_days'])
    #     category, business_info = tool_get_business_meta(state['small_id'])
    #
    #     if PostType.HOLIDAY_POST.name in categories and holidays and total > 0:
    #         pass
    #     else:
    #         # error = HolidayOutput(post='',
    #         #                       keywords='',
    #         #                       event='',
    #         #                       error_message='Validation Failure while generating Holiday Posts').model_dump()
    #         # error['source'] = 'HOLIDAY_POST'
    #
    #         return {"holiday_outputs": [], # error
    #                 "holiday_post_count": 0,
    #                 "holidays": holidays,
    #                 "business_category": category,
    #                 "business_info": json.dumps(business_info)}
    #
    #     holiday_count = len(holidays)
    #     user_prompts = "\n".join(state["prompt_config"].get("holiday", []))
    #     results = []
    #     parser = JsonOutputParser(pydantic_object=HolidayOutput)
    #
    #     for holiday in holidays:
    #             if user_prompts:
    #                 user_prompts = "Keep the above instructions in mind. Below are some special instructions requested by the user, separated by new line. If any conflicting instructions occur, prioritise the above instructions. If you cannot follow some instructions, then ignore that and inside <error_message> you can output why you couldn't follow some instruction if any.\n\n" + user_prompts
    #
    #             format_instructions_local = parser.get_format_instructions()
    #             system_content = (
    #                 f"{holiday_system_prompt.format(holiday=holiday['holiday'], businessDetails=business_info)}\n\n"
    #                 f"{keyword_generator_system}"
    #                 f"Return your response as JSON according to these instructions:\n{format_instructions_local}"
    #             )
    #
    #             sys_msg = SystemMessage(content=system_content)
    #             raw_result = self.llm_holiday.invoke([sys_msg, HumanMessage(content=user_prompts)])
    #
    #             try:
    #                 # Parse the JSON result directly
    #                 parsed_result = parser.parse(raw_result.content)
    #                 parsed_result['source'] = 'HOLIDAY'
    #                 results.append(parsed_result)
    #             except Exception as e:
    #                 # If parsing fails, create a fallback response
    #                 error_msg = HolidayOutput(
    #                     post="",
    #                     keywords="",
    #                     error_message=f"Error parsing output: {str(e)}"
    #                 )
    #                 results.append(error_msg.model_dump())
    #
    #     return {"holiday_outputs": results,
    #             "holiday_post_count": holiday_count,
    #             "holidays": holidays,
    #             "business_category": category,
    #             "business_info": json.dumps(business_info)}

    # def get_trends_agent(self, state: MessagesState) -> dict:
    #     """
    #     Creates trending posts for a given business.
    #     """
    #     count = state['trending_post_count']
    #     business_name = state['business_name']

    #     if count == 0:
    #         return {"trending_outputs": []}

    #     results = []
    #     tools = [tool_fetch_business_trends]
    #     agent = initialize_agent(
    #         tools=tools,
    #         llm=self.llm_trending,
    #         agent=AgentType.OPENAI_FUNCTIONS,
    #         verbose=True
    #     )
    #     user_prompt = state['prompt_config'].get('TRENDING')
    #     business_category = state['business_category']
    #     prompt = f"""Create {count} social media posts using content from the latest trends for the given business category.
    #     Check ``{business_category}`` data using the `tool_fetch_business_trends` tool. Use the exact name of the category while searching.
    #     Once the data is retrieved:
    #     1. Use recent trends (preferably last_24_hours or last_48_hours, but include relevant last_7_days too).
    #     2. Generate posts tailored to the **business context**, using the trends data as the core message.
    #     3. Add business-relevant value or a call-to-action (CTA) that aligns with the trend.
    #     4. Keep the tone informative, engaging, and aligned with industry tone (e.g., compassionate for senior care, friendly for pet care).

    #     Example CTAs: "Learn more", "Schedule a visit", "Ask us today", "Explore our programs", etc.
    #     {format_instructions_list}"""
    #     if user_prompt:
    #         prompt = prompt + f"Below are the instructions given by the user as constrainsts: 'User instructions: {user_prompt}'"
    #     sys_msg = SystemMessage(
    #         content="You are a helpful assistant for generating posts according to trends. First, use the tool `tool_fetch_business_trends` to get the trends data.")
    #     messages = [sys_msg, HumanMessage(content=prompt)]
    #     result = agent.run(messages)
    #     if result:
    #         parsed_result = output_parser_list.parse(result)
    #         results.append(parsed_result)
    #         parsed_results_flatten = []
    #         for i in results:
    #             post_contents = i.posts
    #             for j in post_contents:
    #                 j = j.model_dump()
    #                 j['source'] = "TRENDS"
    #                 parsed_results_flatten.extend([j])
    #         return {"trending_outputs": parsed_results_flatten}

    #     return {"error": f"No trends data found for business: {business_name}"}

    def get_trends_agent(self, state: MessagesState) -> dict:
        """
        Creates trending posts for a given business.
        """
        # print("DATA : ", state)
        count = state['trending_post_count']
        recency = state['number_of_days'] # Duration -> insidetrending_topics -> tool_config
        business_name = state['business_name']
        industry = state['business_category']
        business_info_str = state['business_info']
        business_info_dict = json.loads(business_info_str)
        sub_industry = str(business_info_dict['subCategories'])



        if count == 0:
            return {"trending_outputs": []}
        results = []
        tools = [tool_fetch_business_trends]
        agent = initialize_agent(
            tools=tools,
            llm=self.llm_trending,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True
        )
        user_prompt = state['prompt_config'].get('TRENDING')
        business_category = state['business_category']
        prompt = f"""Create {count} social media posts using content from the latest trends for the given business name {business_name}.
        Check ``{business_name} {industry} {sub_industry} {recency}`` data using the `tool_fetch_business_trends` tool. Use the exact name of the business_name, industry, sub-industry while searching.
        Once the data is retrieved:
        1. Use the "selected_topics" key which contains the key called "topic", based on which you need to create a post
        2. Generate posts tailored to the **business context**, using the trends data as the core message.
        3. Add business-relevant value or a call-to-action (CTA) that aligns with the trend.
        4. Keep the tone informative, engaging, and aligned with industry tone (e.g., compassionate for senior care, friendly for pet care).

        Example CTAs: "Learn more", "Schedule a visit", "Ask us today", "Explore our programs", etc.
        {format_instructions_list}"""
        print("PROMPT : ", prompt)
        if user_prompt:
            prompt = prompt + f"Below are the instructions given by the user as constrainsts: 'User instructions: {user_prompt}'"
        sys_msg = SystemMessage(
            content="You are a helpful assistant for generating posts according to trending topics. First, use the tool `tool_fetch_business_trends` to get the trending topics data.")
        messages = [sys_msg, HumanMessage(content=prompt)]
        result = agent.run(messages)
        if result:
            parsed_result = output_parser_list.parse(result)
            results.append(parsed_result)
            parsed_results_flatten = []
            for i in results:
                post_contents = i.posts
                for j in post_contents:
                    j = j.model_dump()
                    j['source'] = "TRENDS"
                    parsed_results_flatten.extend([j])
            return {"trending_outputs": parsed_results_flatten}

        return {"error": f"No trends data found for business: {business_name}"}
    
    ############# Updated Code with Tools ###############################
    def get_competitor_agent(self, state: MessagesState) -> dict:
            """
            Retrieves competitor posts (company-specific events, testimonials, seasonal offers) for a given business.
            """
            count = state['competitor_post_count']
            if count == 0:
                return {"competitor_outputs": []}
            results = []

            tool_names = [item["name"] for item in state["tools"]["COMP"]]
            # Filter functions and descriptions from TOOLS_REGISTRY
            tool_functions = [TOOLS_REGISTRY[name]["function"] for name in tool_names if name in TOOLS_REGISTRY]
            descriptions = {name: TOOLS_REGISTRY[name]["description"] for name in tool_names if name in TOOLS_REGISTRY}
            agent = initialize_agent(
                tools=tool_functions,
                llm=self.llm_competitor,
                agent=AgentType.OPENAI_FUNCTIONS,
                verbose=True
            )
            user_prompt = state['prompt_config'].get('competitor')
            business_name = state['business_name']

            system_prompt = competitor_system_prompt.format(count=count,business_name=business_name, tools_list=descriptions, config=state['tools']['COMP'], format_instructions_list=format_instructions_list)
            prompt = f"""create {count} post(s) based on competitor posts and instructions provided.
            Follow the config instructions stricly. \
            Strictly follow the Output format instuctions: {format_instructions_list}"""
            if user_prompt:
                prompt = default_user_prompt+ f"Below are the instructions given by the user as constrainsts: 'User instructions: {user_prompt}'"
            sys_msg = SystemMessage(
                content=system_prompt
                )
            messages = [sys_msg, HumanMessage(content=prompt)]
            result = agent.run(messages)
            if result:
                parsed_result = output_parser_list.parse(result)
                results.append(parsed_result)
                parsed_results_flatten = []
                if len(results) == 0:
                    print("Could find any useful competitor post to generate a new post.")
                    return {"competitor_outputs": []}
                for i in results:
                    post_contents = i.posts
                    for j in post_contents:
                        j = j.model_dump()
                        j['source'] = "COMPETITORS"
                        parsed_results_flatten.extend([j])
                return {"competitor_outputs": parsed_results_flatten}

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

        batch_parser = JsonOutputParser(pydantic_object=BusinessBatchOutput)

        for i in range(0, count, 5):
            batch_size = min(5, count - i)
            if user_prompts:
                user_prompts = default_user_prompt + user_prompts

            format_instructions_local = batch_parser.get_format_instructions()

            system_content = (
                f"{business_idea_system.format(num=batch_size, business_details=business_info)}\n\n"
                # f"{keyword_generator_system}"
                f"Return your response as JSON according to these instructions:\n{format_instructions_local}"
            )

            sys_msg = SystemMessage(content=system_content)
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


    # def repurpose_agent(self, state: MessagesState) -> dict:
    #     count = state["repurpose_post_count"]
    #     enterpriseId = state['long_id']
    #     if count == 0:
    #         return {"repurpose_outputs": []}

    #     # repurpose_topics = self._get_repurpose_topics(count)
    #     own_top_perfroming_posts = get_repurposed_posts(enterpriseId, count)

    #     user_prompts = "\n".join(state["prompt_config"].get("REPURPOSED_POST", []))
    #     results = []
    #     parser = JsonOutputParser(pydantic_object=RepurposeOutput)

    #     for post in own_top_perfroming_posts:
    #         topic_prompt = f"Create a social media post using the old post."

    #         if user_prompts:
    #             topic_prompt = topic_prompt + default_user_prompt + user_prompts

    #         format_instructions_local = parser.get_format_instructions()
    #         system_content = (
    #             f"{repurposed_post_system.format(post=post['postText'])}"
    #             f"{keyword_generator_system}"
    #             f"Return your response as JSON according to these instructions:\n{format_instructions_local}"
    #         )

    #         sys_msg = SystemMessage(content=system_content)
    #         raw_result = self.llm_repurpose.invoke([sys_msg, HumanMessage(content=topic_prompt)])

    #         try:
    #             # Parse the JSON result directly
    #             parsed_result = parser.parse(raw_result.content)
    #             parsed_result['source'] = 'REPURPOSED'

    #             results.append(parsed_result)
    #         except Exception as e:
    #             # If parsing fails, create a fallback response
    #             error_msg = RepurposeOutput(
    #                 post="",
    #                 keywords="",
    #                 # topic=topic,
    #                 error_message=f"Error parsing output: {str(e)}"
    #             )
    #             results.append(error_msg.model_dump())

    #     return {"repurpose_outputs": results}

    def repurpose_agent_tool(self, state: MessagesState) -> dict:
        count = state["repurpose_post_count"]
        enterpriseId = state['small_id']
        tool_config = state['tools']
        tools = [tool_get_useful_posts]
        channels = []
        config = {}

        if tool_config.get('REPURPOSED_POST', []):
            for i in tool_config.get('REPURPOSED_POST'):
                channels.append(i['name'].replace('Get Top performing posts - ', ''))

            config = tool_config.get('REPURPOSED_POST')[0]['config']

        if count == 0 or not channels:
            return {"repurpose_outputs": [], "repurpose_post_count": 0}

        results = []
        parser = JsonOutputParser(pydantic_object=RepurposeBatch)

        system_content = (f"{general_system_prompt}"
                        # f"{keyword_generator_system}"
                        f"{repurposed_post_system}"
                        f"{tools_repurpose_prompt}"
                        f'''Return your response as JSON according to these instructions:\n{parser.get_format_instructions().replace("{", "{{").replace("}", "}}")}''')

        user_prompts = "\n".join(state["prompt_config"].get("REPURPOSED_POST", []))
        if user_prompts:
            user_prompts = default_user_prompt + user_prompts

        input_prompt = (f'\n\n Do not generate more than {count} posts.\n'
                f'EnterpriseId: {str(enterpriseId)}\n Page Size: {config["num_posts"]/len(channels)}\n'
                f'Channels: {channels}\n Time period: {"last " + str(config["duration"]) + " days"}'
                f'\n{user_prompts}')

        # Create the prompt template with system content
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_content),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        # Create the OpenAI Functions agent
        agent = create_openai_functions_agent(
            llm=self.llm_repurpose,
            tools=tools,
            prompt=prompt
        )

        # Create the agent executor
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=tools,
            verbose=True
        )

        # Run the agent with just the input
        ai_response = agent_executor.invoke({"input": input_prompt})

        try:
            # Parse the JSON result directly
            parsed_result = parser.parse(ai_response['output'])
            if parsed_result.get('error'):
                print('Could not find any posts to repurpose.')
            else:
                for post in parsed_result['posts']:
                    post['source'] = 'REPURPOSED'
                    results.append(post)

        except Exception as e:
            error_msg = RepurposeOutput(
                post="",
                keywords="",
                error_message=f"Error parsing output: {str(e)}"
            )
            results.append(error_msg.model_dump())

        return {"repurpose_outputs": results, "repurpose_post_count": len(results)}

    def _process_single_post(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helper function to process a single post.
        This will be executed in parallel by the threads.
        """
        try:
            keywords_result = keyword_generator(
                post['post'],
                "" if post.get('source') != 'HOLIDAY' else 'holiday post'
            )
            keywords = keywords_result.get('keywords', '')

            image_url = self._get_image_for_post(keywords)

            return {
                "content": post,
                "source": post.get('source'),  # Use .get for safety if 'source' might be missing
                "keywords": keywords,
                "image_url": image_url
            }
        except Exception as e:
            # Handle exceptions for a single post, e.g., log and return a specific error structure
            print(f"Error processing post {post.get('id', 'N/A')}: {e}")  # Assuming post might have an 'id'
            return {
                "content": post,
                "source": post.get('source'),
                "keywords": "ERROR_GENERATING_KEYWORDS",
                "image_url": "ERROR_FETCHING_IMAGE",
                "error": str(e)
            }

    def combine_posts(self, state: Dict[str, List[Dict[str, Any]]]) -> dict:  # Using Dict for MessagesState
        all_posts = (state.get("holiday_outputs", []) +
                     state.get("business_outputs", []) +
                     state.get("repurpose_outputs", []) +
                     state.get("competitor_outputs", []) +
                     state.get("trending_outputs", []))

        print(f"Finding Image Recommendations for {str(len(all_posts))} Generated Posts")

        enriched = []

        # Using ThreadPoolExecutor to parallelize the processing of each post
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            # map will apply _process_single_post to each item in all_posts
            # and returns results in the order of the input.
            # It submits all tasks at once.
            future_to_post_processor = {executor.submit(self._process_single_post, post): post for post in all_posts}

            # If you want to process results as they complete (potentially out of order):
            # for future in concurrent.futures.as_completed(future_to_post_processor):
            #     try:
            #         enriched_post = future.result()
            #         enriched.append(enriched_post)
            #     except Exception as exc:
            #         original_post = future_to_post_processor[future]
            #         print(f"Post generated an exception: {original_post.get('id', 'N/A')} - {exc}")
            #         # Optionally append an error placeholder or skip
            #         enriched.append({
            #             "content": original_post, "source": original_post.get('source'),
            #             "error": str(exc), "keywords": "", "image_url": ""
            #         })

            # If order matters and you want to collect all results (map is simpler for this):
            results_iterator = executor.map(self._process_single_post, all_posts)
            enriched = list(results_iterator)  # Convert iterator to list

        return {"combined_posts": enriched}

    def fetch_n_btp(self, state: MessagesState):
        total_posts = state['combined_posts']
        n_posts = len(total_posts)

        time_slots = fetch_btp()
        slots = get_best_time_slots_next_7_days(time_slots['timeSlots'], n_posts)
        for post, slot in zip(total_posts, slots):
            post['slot'] = slot

        return {'combined_posts': total_posts}

    def generate(self, input_payload: dict) -> dict:
        return self.graph.invoke(input_payload)


# input_payload = {
#     "total_post": 6,
#     'small_id': '1148914',
#     'long_id': '169030216166956',
#     'business_name': 'Village Pet Care',
#     'number_of_days': 10,
#     # "business_info": "We provide expert dental care and cleaning services with cutting-edge equipment and experienced staff.",
#     # "business_name": "Aspen Dental",
#     # "business_category":"dental_us",
#     #"categories": ["HOLIDAY_POST", "BUSINESS_IDEAS_POST", "REPURPOSED_POST", "TRENDING", "COMP"],
#     "categories": ["HOLIDAY_POST", "BUSINESS_IDEAS_POST", "REPURPOSED_POST", "TRENDING", "COMP"],
#     "prompt_config" : {
#         "HOLIDAY_POST" : ['Generate Holiday Posts'],
#         "BUSINESS_IDEAS_POST": ["We are offering discount of 20% this week. Make sure to include that"],
#         "REPURPOSED_POST": [],
#         "TRENDING": [],
#         "COMP": []
#     },
#     "tools": {
#             "HOLIDAY_POST": [
#                 {
#                 "name": "Get Upcoming Holidays"
#                 }
#             ],
#             "REPURPOSED_POST": [
#                 {
#                     "name": "Get Top performing posts - all",
#                     "config": {
#                         "num_posts": 5,
#                         "evaluation_metric": "Engagement"
#                     }
#                 }
#             ],
#             "COMP": [
#                 {
#                    "name": "Get Top performing posts - facebook",
#                    "config": {
#                         "evaluation_metric": "Engagement",
#                         "date_range": "last_30_days"
#                     }
#                 },
#                 {
#                    "name": "Get Top performing posts - instagram",
#                    "config": {
#                         "evaluation_metric": "Engagement",
#                         "date_range": "last_30_days"
#                     }
#                 }
#             ],
#             "BUSINESS_IDEAS_POST": [
#                 {
#                 "name": "Business Context"
#                 }
#             ],
#             "TRENDING": [
#                 {
#                 "name": "Fetch Trending Topics"
#                 }
#             ]
#             }
#}
input_payload= {
  "total_post": 7,
  "small_id": "1148914",
  "long_id": "169030216166956",
  "business_name": "Village Pet Care",
  "holidays": [
    {
      "date": "2025-03-09",
      "holiday": "Diwali"
    },
    {
      "date": "2025-03-17",
      "holiday": "St. Patrick's Day"
    }
  ],
  "number_of_days": 10,
  "categories": [
    "BUSINESS_IDEAS_POST",
    "HOLIDAY_POST",
    "REPURPOSED_POST",
    # "COMP",
    # "TRENDING"
  ],
  "prompt_config": {
    "BUSINESS_IDEAS_POST": [
      " Generate post ideas based on the business context."
    ],
    "HOLIDAY_POST": [
      " Generate post for upcoming holidays."
    ],
    "REPURPOSED_POST": [
      " Generate new posts based on your top performing posts."
    ],
    "COMP": [
      " Generate new posts based on your competitors' top performing posts."
    ],
    "TRENDING": [
      " Create posts based on the latest trends"
    ]
  },
  "tools": {
    "HOLIDAY_POST": [
      {
        "name": "Get Upcoming Holidays",
        "config": {
          "include_business_context": True
        }
      }
    ],
    "REPURPOSED_POST": [
      {
        "name": "Get Top performing posts - facebook",
        "config": {
          "num_posts": 10,
          "duration": "30",
          "evaluation_metric": "Engagement"
        }
      },
      {
        "name": "Get Top performing posts - twitter",
        "config": {
          "num_posts": 10,
          "duration": "30",
          "evaluation_metric": "Engagement"
        }
      },
      {
        "name": "Get Top performing posts - instagram",
        "config": {
          "num_posts": 10,
          "duration": "30",
          "evaluation_metric": "Engagement"
        }
      }
    ],
    "BUSINESS_IDEAS_POST": [
      {
        "name": "Business Context",
        "config": {
          "enabled": True
        }
      }
    ],
    "COMP": [
      {
        "name": "Get Top performing posts - facebook",
        "config": {
          "num_posts": 20,
          "duration": "30",
          "evaluation_metric": "Engagement"
        }
      },
      {
        "name": "Get Top performing posts - instagram",
        "config": {
          "num_posts": 20,
          "duration": "30",
          "evaluation_metric": "Engagement"
        }
      }
    ],
    "TRENDING": [
      {
        "name": "Fetch Trending Topics",
        "config": {
          "num_posts": 20,
          "duration": "30"
        }
      }
    ]
  }
}
# 'make diwali post very bright. use colorful emojis', 'st. patricks post should alcohol focused. Connect it to some dental health concern.'


# social_agent = SocialMediaPostGenerator()
#
# posts = social_agent.generate(input_payload)
#
# for post in posts["combined_posts"]:
#     print(f"Source:{post['source']}\nContent:\n{post['content']}\nImage: {post['image_url']}\n{'-'*50}")
