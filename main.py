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

def chat_completion(user_content: str, system_content: str = "You are a helpful assistant.", model: str = "o4-mini") -> str:
    """
    Helper function to call OpenAI's chat completion API with custom system instructions and model.
    """
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

@app.post("/mcp/summarize", response_model=SummarizeResponse)
def summarize(request: SummarizeRequest):
    summary = chat_completion(
        user_content=f"Summarize the following text:\n{request.text}",
        system_content="You are a helpful assistant that summarizes text.",
        model="o4-mini"
    )
    return SummarizeResponse(summary=summary)

@app.post("/mcp/pirate_summarize", response_model=SummarizeResponse)
def pirate_summarize(request: SummarizeRequest):
    summary = chat_completion(
        user_content=f"Summarize the following text in the style of a pirate:\n{request.text}",
        system_content="You are a helpful assistant that summarizes text in the style of a pirate. Use pirate language and expressions.",
        model="o4-mini"
    )
    return SummarizeResponse(summary=summary)
