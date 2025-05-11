from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from pydantic import BaseModel
import os
import openai
from fastapi.responses import JSONResponse

app = FastAPI()

# MCP handshake endpoint: lets clients know the server speaks MCP
@app.get("/mcp/handshake")
def handshake():
    return {"protocol": "model-context-protocol", "version": "1.0"}

# Example context model (expandable)
class WorkspaceContext(BaseModel):
    root_path: str
    open_files: list[str]
    project_name: str | None = None
    language: str | None = None
    capabilities: list[str] | None = None

# MCP context endpoint: returns a simple workspace context
@app.get("/mcp/context", response_model=WorkspaceContext)
def get_context():
    # Dynamically list files in the files/ directory as open_files
    open_files = [f for f in os.listdir(FILES_DIR) if os.path.isfile(os.path.join(FILES_DIR, f))]
    return WorkspaceContext(
        root_path=FILES_DIR,
        open_files=open_files,
        project_name="MCP Demo",
        language="python",
        capabilities=["summarize", "list_files", "file_content", "create_file", "upload_pdf"]
    )

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

class FileRequest(BaseModel):
    filename: str

class FileContentResponse(BaseModel):
    content: str

class FileListResponse(BaseModel):
    files: list[str]

class FileCreateRequest(BaseModel):
    filename: str
    content: str

class FileCreateResponse(BaseModel):
    success: bool
    message: str

class CapabilitiesResponse(BaseModel):
    capabilities: list[str]
    models: list[str] | None = None
    file_types: list[str] | None = None

FILES_DIR = os.path.join(os.getcwd(), "files")

# Update file listing to use files/ directory
@app.get("/mcp/capabilities", response_model=CapabilitiesResponse)
def get_capabilities():
    return CapabilitiesResponse(
        capabilities=["summarize", "pirate_summarize", "list_files", "file_content", "create_file", "upload_pdf", "intent"],
        models=["o4-mini"],
        file_types=[".py", ".txt", ".pdf"]
    )

class IntentRequest(BaseModel):
    action: str
    target: str | None = None
    parameters: dict | None = None

class IntentResponse(BaseModel):
    result: str
    success: bool

@app.post("/mcp/intent", response_model=IntentResponse)
def handle_intent(request: IntentRequest):
    # Summarize a file
    if request.action == "summarize_file" and request.target:
        file_path = os.path.abspath(os.path.join(FILES_DIR, request.target))
        if not file_path.startswith(FILES_DIR) or not os.path.isfile(file_path):
            return IntentResponse(result="File not found or invalid path.", success=False)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        summary = chat_completion(
            user_content=f"Summarize the following file content:\n{content}",
            system_content="You are a helpful assistant that summarizes file content.",
            model="o4-mini"
        )
        return IntentResponse(result=summary, success=True)
    # Pirate summarize a file
    if request.action == "pirate_summarize_file" and request.target:
        file_path = os.path.abspath(os.path.join(FILES_DIR, request.target))
        if not file_path.startswith(FILES_DIR) or not os.path.isfile(file_path):
            return IntentResponse(result="File not found or invalid path.", success=False)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        summary = chat_completion(
            user_content=f"Summarize the following text in the style of a pirate:\n{content}",
            system_content="You are a helpful assistant that summarizes text in the style of a pirate. Use pirate language and expressions.",
            model="o4-mini"
        )
        return IntentResponse(result=summary, success=True)
    # List files
    if request.action == "list_files":
        files = [f for f in os.listdir(FILES_DIR) if os.path.isfile(os.path.join(FILES_DIR, f))]
        return IntentResponse(result="\n".join(files), success=True)
    # Get file content
    if request.action == "file_content" and request.target:
        file_path = os.path.abspath(os.path.join(FILES_DIR, request.target))
        if not file_path.startswith(FILES_DIR) or not os.path.isfile(file_path):
            return IntentResponse(result="File not found or invalid path.", success=False)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return IntentResponse(result=content, success=True)
    # Create file
    if request.action == "create_file" and request.parameters:
        filename = request.parameters.get("filename")
        content = request.parameters.get("content", "")
        if not filename:
            return IntentResponse(result="Missing filename.", success=False)
        safe_path = os.path.abspath(os.path.join(FILES_DIR, filename))
        if not safe_path.startswith(FILES_DIR):
            return IntentResponse(result="Invalid file path.", success=False)
        try:
            with open(safe_path, "w", encoding="utf-8") as f:
                f.write(content)
            return IntentResponse(result="File created successfully.", success=True)
        except Exception as e:
            return IntentResponse(result=f"Error: {str(e)}", success=False)
    # Upload PDF (base64 encoded in parameters)
    if request.action == "upload_pdf" and request.parameters:
        import base64
        filename = request.parameters.get("filename")
        filedata = request.parameters.get("filedata")
        if not filename or not filedata or not filename.lower().endswith('.pdf'):
            return IntentResponse(result="Missing filename or filedata, or not a PDF.", success=False)
        safe_path = os.path.abspath(os.path.join(FILES_DIR, filename))
        if not safe_path.startswith(FILES_DIR):
            return IntentResponse(result="Invalid file path.", success=False)
        try:
            with open(safe_path, "wb") as f:
                f.write(base64.b64decode(filedata))
            return IntentResponse(result="PDF uploaded successfully.", success=True)
        except Exception as e:
            return IntentResponse(result=f"Error: {str(e)}", success=False)
    return IntentResponse(result=f"Action '{request.action}' not supported.", success=False)
