import time
from collections.abc import AsyncIterator
from logging import getLogger
from typing import Any, Dict

from agents import Runner, trace
from agents.voice import (
    TTSModelSettings,
    VoicePipeline,
    VoicePipelineConfig,
    VoiceWorkflowBase,
)
from app.agent_config import starting_agent
from app.security import security_guardrail, secure_endpoint
from app.utils import (
    WebsocketHelper,
    concat_audio_chunks,
    extract_audio_chunk,
    is_audio_complete,
    is_new_audio_chunk,
    is_new_text_message,
    is_sync_message,
    is_text_output,
    process_inputs,
)
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel


from dotenv import load_dotenv

# When .env file is present, it will override the environment variables
load_dotenv(dotenv_path="../.env", override=True)

app = FastAPI()

logger = getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API requests
class ChatRequest(BaseModel):
    message: str
    user_id: str = None
    agent_type: str = "rent"  # "rent" or "sale"

class SecurityStatusResponse(BaseModel):
    user_id: str
    warnings: int
    is_blocked: bool
    max_warnings: int

class Workflow(VoiceWorkflowBase):
    def __init__(self, connection: WebsocketHelper):
        self.connection = connection

    async def run(self, input_text: str, user_id: str = None) -> AsyncIterator[str]:
        # Security check on input
        allowed, filtered_message, security_check = await security_guardrail.filter_input(
            input_text, user_id
        )
        
        if not allowed:
            # Send security warning to user
            await self.connection.send_error_message(filtered_message)
            return
        
        # Log security event if needed
        if security_check.risk_level.value != "safe":
            await security_guardrail.log_security_event(
                "input_warning", user_id, {
                    "risk_level": security_check.risk_level.value,
                    "reason": security_check.reason,
                    "original_message": input_text[:100] + "..." if len(input_text) > 100 else input_text
                }
            )

        conversation_history, latest_agent = await self.connection.show_user_input(
            filtered_message
        )

        output = Runner.run_streamed(
            latest_agent,
            conversation_history,
        )

        response_buffer = ""
        async for event in output.stream_events():
            await self.connection.handle_new_item(event)

            if is_text_output(event):
                response_buffer += event.data.delta  # type: ignore
                yield event.data.delta  # type: ignore

        # Security check on complete output
        if response_buffer:
            allowed_output, filtered_response, output_check = await security_guardrail.filter_output(
                response_buffer, {"user_id": user_id, "agent": latest_agent.name}
            )
            
            if not allowed_output:
                # Send safe alternative response
                await self.connection.send_error_message(filtered_response)
                await security_guardrail.log_security_event(
                    "output_blocked", user_id, {
                        "risk_level": output_check.risk_level.value,
                        "reason": output_check.reason,
                        "agent": latest_agent.name
                    }
                )
                return
            
            # If output was modified (warning added), stream the additional content
            if filtered_response != response_buffer:
                additional_content = filtered_response[len(response_buffer):]
                if additional_content:
                    await self.connection.stream_response(additional_content, is_text=True)

        await self.connection.text_output_complete(output, is_done=True)


@app.post("/chat")
@secure_endpoint
async def chat_endpoint(request: ChatRequest):
    """
    HTTP endpoint for chat with security guardrails
    """
    try:
        # Security check on input
        allowed, filtered_message, security_check = await security_guardrail.filter_input(
            request.message, request.user_id
        )
        
        if not allowed:
            return JSONResponse(
                status_code=400,
                content={
                    "error": filtered_message,
                    "security_info": {
                        "risk_level": security_check.risk_level.value,
                        "reason": security_check.reason
                    }
                }
            )
        
        # Select appropriate agent
        from app.custom_agent.custom_agent import rent_support_agent, sale_support_agent
        agent = rent_support_agent if request.agent_type == "rent" else sale_support_agent
        
        # Run the agent
        output = Runner.run_sync(agent, filtered_message)
        response_text = output.data if hasattr(output, 'data') else str(output)
        
        # Security check on output
        allowed_output, filtered_response, output_check = await security_guardrail.filter_output(
            response_text, {"user_id": request.user_id, "agent": agent.name}
        )
        
        if not allowed_output:
            await security_guardrail.log_security_event(
                "output_blocked", request.user_id, {
                    "risk_level": output_check.risk_level.value,
                    "reason": output_check.reason,
                    "agent": agent.name
                }
            )
            return JSONResponse(
                status_code=500,
                content={"error": filtered_response}
            )
        
        return {
            "response": filtered_response,
            "agent": agent.name,
            "security_status": "safe" if security_check.risk_level.value == "safe" else "warning"
        }
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": security_guardrail.get_safe_error_message("technical")}
        )

@app.get("/security/status/{user_id}")
async def get_user_security_status(user_id: str) -> SecurityStatusResponse:
    """
    Get security status for a user
    """
    status = security_guardrail.get_user_status(user_id)
    return SecurityStatusResponse(**status)

@app.post("/security/reset/{user_id}")
async def reset_user_security(user_id: str):
    """
    Reset security warnings for a user (admin endpoint)
    """
    security_guardrail.reset_user_warnings(user_id)
    return {"message": f"Security status reset for user {user_id}"}

@app.get("/security/health")
async def security_health_check():
    """
    Health check endpoint for security system
    """
    return {
        "status": "healthy",
        "guardrail_active": True,
        "timestamp": time.time(),
        "blocked_users": len(security_guardrail.blocked_users),
        "total_warnings": sum(security_guardrail.warning_counts.values())
    }

@app.websocket("/ws")
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    with trace("Voice Agent Chat"):
        await websocket.accept()
        connection = WebsocketHelper(websocket, [], starting_agent)
        audio_buffer = []
        user_id = None  # Should be extracted from authentication or query params

        workflow = Workflow(connection)
        while True:
            try:
                message = await websocket.receive_json()
                print(f"Received message: {message}")
                
                # Extract user_id if provided
                if "user_id" in message:
                    user_id = message["user_id"]
                    
            except WebSocketDisconnect:
                print("Client disconnected")
                return

            # Handle text based messages
            if is_sync_message(message):
                connection.history = message["inputs"]
                if message.get("reset_agent", False):
                    connection.latest_agent = starting_agent
            elif is_new_text_message(message):
                user_input = process_inputs(message, connection)
                async for new_output_tokens in workflow.run(user_input, user_id):
                    await connection.stream_response(new_output_tokens, is_text=True)

            # Handle a new audio chunk
            elif is_new_audio_chunk(message):
                audio_buffer.append(extract_audio_chunk(message))

            # Send full audio to the agent
            elif is_audio_complete(message):
                start_time = time.perf_counter()

                def transform_data(data):
                    nonlocal start_time
                    if start_time:
                        print(
                            f"Time taken to first byte: {time.perf_counter() - start_time}s"
                        )
                        start_time = None
                    return data

                audio_input = concat_audio_chunks(audio_buffer)
                output = await VoicePipeline(
                    workflow=workflow,
                    config=VoicePipelineConfig(
                        tts_settings=TTSModelSettings(
                            buffer_size=512, transform_data=transform_data
                        )
                    ),
                ).run(audio_input)
                async for event in output.stream():
                    await connection.send_audio_chunk(event)

                audio_buffer = []  # reset the audio buffer


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
