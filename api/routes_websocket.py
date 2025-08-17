from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .integration import mas_integration
import logging
import json

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для real-time обмена сообщениями"""
    await websocket.accept()
    try:
        while True:
            # Ждем сообщение от клиента
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                user_message = message_data.get("message", "")
                user_id = message_data.get("user_id", "websocket_user")
                
                # Обрабатываем через MAS
                response = await mas_integration.process_message(user_message, user_id)
                
                # Отправляем ответ
                await websocket.send_json({
                    "type": "response",
                    "message": response,
                    "agent": "communicator"
                })
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                logger.error(f"WebSocket processing error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass


@router.websocket("/ws/visualization")
async def websocket_visualization(websocket: WebSocket):
    """WebSocket для визуализации мыслительного процесса агентов"""
    # TODO: Implement visualization websocket
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Process visualization commands
            await websocket.send_json({"status": "not_implemented"})
    except WebSocketDisconnect:
        pass