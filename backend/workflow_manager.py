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
    active_tools: List[str]

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
    posts: List[PostContent]

class HolidayOutput(BaseModel):
    post: str = Field(description="The post generated")
    keywords: str = Field(description="Keywords for the generated post")
    event: str = Field(description="The name of the holiday or event on which the post is generated")
    error_message: Optional[str] = Field(description="Optional error message if there was an issue", default=None)

class HolidayBatch(BaseModel):
    posts: Optional[List[HolidayOutput]]
    business_category: str = Field(description="The business main category if available. If not return empty string")
    business_info: dict = Field(description="The rest of the business info apart from the category, in a dictionary format. If not, return empty dictionary")
    error: bool = Field(description="Should be true if no available holiday and no post is generated. Else, False")

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
        self.tools = [get_upcoming_week_holidays, get_business_meta]

        self.graph = self._build_graph()


    def _get_repurpose_topics(self, n: int) -> List[str]:
        return [f"Repurpose Topic {i + 1}" for i in range(n)]

    def _get_image_for_post(self, content: str) -> str:
        return search_pixabay_images(content)


    def _build_graph(self):
        builder = StateGraph(MessagesState)
        # tool_executor_node = ToolNode(self.tools)

        builder.add_node("holiday_agent", self.holiday_agent_tool)
        # builder.add_node("tools_node", tool_executor_node)

        builder.add_node("allocate_source_count", self.allocate_source_count)
        builder.add_node("repurpose_agent", self.repurpose_agent)
        builder.add_node("competitor_agent", self.get_competitor_agent)
        builder.add_node("trends_agent", self.get_trends_agent)
        builder.add_node("business_agent", self.business_agent)
        builder.add_node("combine_posts_and_add_image", self.combine_posts)
        # builder.add_node("Analyse & Select Best Time to Post", self.fetch_n_btp)

        builder.set_entry_point("holiday_agent")

        # builder.add_conditional_edges(
        #     "holiday_agent", # Source node
        #     self.should_call_tool,  # Function to decide the route
        #     {
        #         "tools_node": "tools_node",   # If should_call_tool returns "tools", go to "tools" node
        #         "allocate_source_count": "allocate_source_count"      # If should_call_tool returns "__end__", go to END
        #     }
        # )

        builder.add_edge("holiday_agent", "allocate_source_count")

        builder.add_edge("allocate_source_count", "repurpose_agent")
        builder.add_edge("allocate_source_count", "competitor_agent")
        builder.add_edge("allocate_source_count", "trends_agent")

        builder.add_edge("repurpose_agent", "business_agent")
        builder.add_edge("competitor_agent", "business_agent")
        builder.add_edge("trends_agent", "business_agent")

        builder.add_edge("business_agent", "combine_posts_and_add_image")

        builder.add_edge("combine_posts_and_add_image", END)
        # builder.add_edge('Analyse & Select Best Time to Post', END)

        return builder.compile()


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
            "trending_post_count": trending_post,
            "trending_outputs": []
        }
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
        num_days = state['number_of_days']
        last_message = state["last_call"]

        if PostType.HOLIDAY_POST.name in categories and total > 0:
            pass
        else:
            # error = HolidayOutput(post='',
            #                       keywords='',
            #                       event='',
            #                       error_message='Validation Failure while generating Holiday Posts').model_dump()
            # error['source'] = 'HOLIDAY_POST'

            return {"holiday_outputs": [], # error
                    "holiday_post_count": 0}

        results = []
        parser = JsonOutputParser(pydantic_object=HolidayBatch)

        system_content = (f"{general_system_prompt}"
                          f"{keyword_generator_system})"
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
            tools=self.tools,
            prompt=prompt
        )

        # Create the agent executor
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            verbose=True
        )

        # Run the agent with just the input
        ai_response = agent_executor.invoke({"input": input_prompt})

        # # Create the agent
        # agent = initialize_agent(
        #     tools=self.tools,
        #     llm=self.llm_holiday,
        #     agent=AgentType.OPENAI_FUNCTIONS,
        #     verbose=True
        # )
        #
        # input_dict = {
        #     "system": system_content,
        #     "input": input_prompt,
        #     "Output Formatter": parser.get_format_instructions()
        # }
        #
        # # Run the agent with the holiday prompt as input
        # ai_response = agent.run(input_dict)
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
    #     holidays = get_upcoming_week_holidays(state['number_of_days'])
    #     category, business_info = get_business_meta(state['small_id'])
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

    def get_trends_agent(self, state: MessagesState) -> dict:
        """
        Creates trending posts for a given business.
        """
        count = state['trending_post_count']
        business_name = state['business_name']

        if count == 0:
            return {"trending_outputs": []}
        results = []
        tools = [fetch_business_trends]
        agent = initialize_agent(
            tools=tools,
            llm=self.llm_trending,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True
        )
        user_prompt = state['prompt_config'].get('TRENDING')
        business_category = state['business_category']
        prompt = f"""Create {count} social media posts using content from the latest trends for the given business category.
        Check ``{business_category}`` data using the `fetch_business_trends` tool. Use the exact name of the category while searching.
        Once the data is retrieved:
        1. Use recent trends (preferably last_24_hours or last_48_hours, but include relevant last_7_days too).
        2. Generate posts tailored to the **business context**, using the trends data as the core message.
        3. Add business-relevant value or a call-to-action (CTA) that aligns with the trend.
        4. Keep the tone informative, engaging, and aligned with industry tone (e.g., compassionate for senior care, friendly for pet care).

        Example CTAs: "Learn more", "Schedule a visit", "Ask us today", "Explore our programs", etc.
        {format_instructions_list}"""
        if user_prompt:
            prompt = prompt + f"Below are the instructions given by the user as constrainsts: 'User instructions: {user_prompt}'"
        sys_msg = SystemMessage(
            content="You are a helpful assistant for generating posts according to trends. First, use the tool `fetch_business_trends` to get the trends data.")
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
        tools = [fetch_business_competitors]
        agent = initialize_agent(
            tools=tools,
            llm=self.llm_competitor,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True
        )
        user_prompt = state['prompt_config'].get('competitor')
        business_name = state['business_name']

        prompt = f"""Create {count} social media posts using content from competitors for the given business.
        Check ``{business_name}`` data using the `fetch_business_competitors` tool. Fill in the competitors' data from the tool response. Use the exact business name when querying.
        Ignore categories such as internal company events, awards, hiring updates, or location openings/closures.
        Focus only on posts that demonstrate value, customer engagement, services, community relevance, or educational insights.
        Adapt the content to include the context relevant to the target business.{format_instructions_list}"""

        if user_prompt:
            prompt = prompt + f"Below are the instructions given by the user as constrainsts: 'User instructions: {user_prompt}'"
        sys_msg = SystemMessage(
            content="You are a helpful assistant for generating posts similar to competitors' posts. First, use the tool `fetch_business_competitors` to get the competitors' data.")
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
                user_prompts = default_user_prompt + user_prompts

            format_instructions_local = batch_parser.get_format_instructions()

            system_content = (
                f"{business_idea_system.format(num=batch_size, business_details=business_info)}\n\n"
                f"{keyword_generator_system}"
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
            'competitor_outputs'] + state['trending_outputs']

        print(" POSt data -- ", all_posts)
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
    "prompt_config" : {
        "HOLIDAY_POST" : ['Generate Holiday Posts'],
        "BUSINESS_IDEAS_POST": [],
        "REPURPOSED_POST": [],
        "TRENDING": [],
        "COMP": []
    }
}
# 'make diwali post very bright. use colorful emojis', 'st. patricks post should alcohol focused. Connect it to some dental health concern.'


social_agent = SocialMediaPostGenerator()

posts = social_agent.generate(input_payload)

for post in posts["combined_posts"]:
    print(f"Source:{post['source']}\nContent:\n{post['content']}\nImage: {post['image_url']}\n{'-'*50}")
