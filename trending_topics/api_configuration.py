from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from enum import Enum
import json

# Import your logic functions
from search_trending_topics import generate_social_media_strategy  # Replace 'your_module' with actual filename if needed

app = FastAPI(title="Trending Topics Generator")

# # Step 1: Define the Enum for recency
# class RecencyEnum(str, Enum):
#     this_week = "This Week"
#     this_month = "This Month"
#     this_quarter = "This Quarter"

class StrategyRequest(BaseModel):
    business_name: str
    industry: str
    sub_industry: str
    country: str = "US"
    city: str = "All Cities"
    state: str = "All States"
    recency: int

# @app.post("/generate-trending-topics")
# def trending_topics(request: StrategyRequest):
#     try:
#         result = generate_social_media_strategy(
#             business_name=request.business_name,
#             industry=request.industry,
#             sub_industry=request.sub_industry,
#             country=request.country,
#             city=request.city,
#             state=request.state,
#             recency=request.recency
#         )
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

import traceback

@app.post("/generate-trending-topics")
def trending_topics(request: StrategyRequest):
    try:
        result = generate_social_media_strategy(
            business_name=request.business_name,
            industry=request.industry,
            sub_industry=request.sub_industry,
            country=request.country,
            city=request.city,
            state=request.state,
            recency=request.recency
        )
        return result
    except Exception as e:
        traceback.print_exc()  # 👈 This will print full error in the server log
        raise HTTPException(status_code=500, detail=str(e))


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, port=8008, host="0.0.0.0",reload=True)