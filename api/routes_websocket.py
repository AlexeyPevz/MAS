from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .integration import mas_integration
from .security import security_manager
import logging
import json

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
	"""WebSocket для real-time обмена сообщениями"""
	# Simple token-based auth via query param
	query_params = dict(websocket.query_params)
	token = query_params.get("token")
	if token:
		try:
			security_manager.verify_token(token)
		except Exception:
			await websocket.close(code=1008)
			return
	await websocket.accept()
	try:
		while True:
			# Ждем сообщение от клиента
			data = await websocket.receive_text()
			# Quick ping-pong support
			if data.strip().lower() == "ping":
				await websocket.send_text("pong")
				continue
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
	await websocket.accept()
	# Store connection
	connections = getattr(websocket_visualization, '_connections', set())
	connections.add(websocket)
	websocket_visualization._connections = connections
	try:
		while True:
			data = await websocket.receive_text()
			try:
				message = json.loads(data)
				if message.get("type") == "ping":
					await websocket.send_json({"type": "pong"})
				elif message.get("type") == "subscribe":
					flow_id = message.get("flow_id")
					if flow_id:
						# Subscribe to flow updates
						await websocket.send_json({
							"type": "subscribed",
							"flow_id": flow_id
						})
				elif message.get("type") == "get_agent_profiles":
					# Get agent profiles
					from config.config_loader import load_config
					config = load_config()
					agents = list(config.get('agents', {}).keys())
					await websocket.send_json({
						"type": "agent_profiles",
						"data": agents
					})
			except json.JSONDecodeError:
				await websocket.send_json({
					"type": "error",
					"message": "Invalid JSON"
				})
	except WebSocketDisconnect:
		# Remove connection
		if hasattr(websocket_visualization, '_connections'):
			websocket_visualization._connections.discard(websocket)