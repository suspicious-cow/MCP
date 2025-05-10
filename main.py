from fastapi import FastAPI
from pydantic import BaseModel

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
