from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import uvicorn
from datetime import datetime
import json
import io
import sys
from Trending_topic.gemini import generate

app = FastAPI(
    title="Trending Topics Generator API",
    description="API for generating trending topics for business social media content",
    version="1.0.0"
)

class PostIdea(BaseModel):
    text: str = Field(..., description="The social media post idea text")

class TrendingTopic(BaseModel):
    trend_name: str = Field(..., description="Name of the trending topic (1-3 words)")
    trend_category: str = Field(..., description="Category of the trend")
    date_time: str = Field(..., description="Date and time in ISO 8601 format")
    post_ideas: List[str] = Field(..., description="List of social media post ideas")
    source_type: str = Field(..., description="Source of the trend")

class TrendingTopicsResponse(BaseModel):
    trending_topics: List[TrendingTopic] = Field(..., description="List of trending topics")

class GenerateRequest(BaseModel):
    business_name: str = Field(..., description="Name of the business")
    industry: str = Field(..., description="Main industry of the business")
    sub_industry: Optional[str] = Field(None, description="Sub-industry specification")
    location: Optional[str] = Field(None, description="Business location")
    date_time: Optional[str] = Field(None, description="Target date and time (YYYY-MM-DD HH:MM:SS)")

@app.post("/generate", response_model=TrendingTopicsResponse)
async def generate_trending_topics(request: GenerateRequest):
    """
    Generate trending topics for a business based on provided parameters.
    
    Returns a list of trending topics with post ideas and metadata.
    """
    try:
        # Capture stdout to get the generate function output
        output = io.StringIO()
        sys.stdout = output
        
        # Call generate function
        generate(
            business_name=request.business_name,
            industry=request.industry,
            sub_industry=request.sub_industry,
            location=request.location,
            date_time=request.date_time
        )
        
        # Restore stdout
        sys.stdout = sys.__stdout__
        
        # Get the output and parse as JSON
        result = output.getvalue().strip()
        
        # Try to find JSON content in the output
        start_idx = result.find('{')
        end_idx = result.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_str = result[start_idx:end_idx]
            try:
                data = json.loads(json_str)
                if "trending_topics" not in data or not isinstance(data["trending_topics"], list):
                    raise HTTPException(
                        status_code=500,
                        detail="Invalid response format from generator"
                    )
                return data
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to parse generator output as JSON"
                )
        else:
            raise HTTPException(
                status_code=500,
                detail="No valid JSON found in generator output"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating trending topics: {str(e)}"
        )

@app.get("/")
async def root():
    """
    Root endpoint providing API information.
    """
    return {
        "name": "Trending Topics Generator API",
        "version": "1.0.0",
        "description": "Generate trending topics for business social media content",
        "endpoints": {
            "/generate": "POST - Generate trending topics",
            "/docs": "GET - OpenAPI documentation",
            "/redoc": "GET - ReDoc documentation"
        }
    }

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True) 