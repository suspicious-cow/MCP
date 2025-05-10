from fastapi import FastAPI, Request
from pydantic import BaseModel
import os
import openai

app = FastAPI()

# MCP handshake endpoint: lets clients know the server speaks MCP
@app.get("/mcp/handshake")
def handshake():
    return {"protocol": "model-context-protocol", "version": "1.0"}

# Example context model (expandable)
class WorkspaceContext(BaseModel):
    root_path: str
    open_files: list[str]

# MCP context endpoint: returns a simple workspace context
@app.get("/mcp/context", response_model=WorkspaceContext)
def get_context():
    # Example: hardcoded context for demo
    return WorkspaceContext(
        root_path="/workspace/MCP",
        open_files=["main.py", "README.md"]
    )

class SummarizeRequest(BaseModel):
    text: str

class SummarizeResponse(BaseModel):
    summary: str

@app.post("/mcp/summarize", response_model=SummarizeResponse)
def summarize(request: SummarizeRequest):
    # Use OpenAI's Chat Completions API to summarize the text
    try:
        response = openai.chat.completions.create(
            model="o4-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes text."},
                {"role": "user", "content": f"Summarize the following text:\n{request.text}"}
            ],
        )
        summary = response.choices[0].message.content.strip()
    except Exception as e:
        summary = f"Error: {str(e)}"
    return SummarizeResponse(summary=summary)
