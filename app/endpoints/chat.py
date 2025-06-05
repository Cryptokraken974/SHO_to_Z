@app.post("/api/chat")
async def api_chat(data: dict):
    prompt = data.get("prompt", "")
    model = data.get("model", "")
    # Placeholder response; integrate with real LLM here
    response = f"Model {model} says: {prompt}"
    return {"response": response}
