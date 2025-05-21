from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn
from workflow_manager import SocialMediaPostGenerator

app = FastAPI(
    title="LangGraph Post Generation Agent",
    description="API to generate social media posts based on selected sources.",
    version="0.1.0"
)

social_agent = SocialMediaPostGenerator()

@app.post("/generate-posts/")
async def generate_posts_endpoint(request: dict):
    """
    Generate social media posts based on the provided configuration.
    """

    try:
        print(f"API: Received request: {request}")
        final_state = social_agent.generate(request)
        return final_state
    except Exception as e:
        print(f"API Error: {str(e)}")
        # Log the full exception for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")


@app.get("/")
async def read_root():
    return {"message": "Welcome to the LangGraph Post Generation Agent API. Use the /docs endpoint for API details."}


if __name__ == "__main__":
    # This part is for running with `python main.py` directly, useful for some environments
    # Uvicorn recommends running via its command line tool for production features.
    uvicorn.run(app, host="0.0.0.0", port=8000)
