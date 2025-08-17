"""
Trading API endpoints for commodity trading operations
API endpoints для операций с сырьевыми товарами
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from api.security import require_permission, auth_user_dependency
from agents.trading_agents import TRADING_AGENTS
from tools.smart_groupchat import SmartGroupChatManager

router = APIRouter(prefix="/api/v1/trading", tags=["trading"])


# Pydantic модели для трейдинга
class TradeRequest(BaseModel):
    """Запрос на создание сделки"""
    commodity: str = Field(..., description="Тип товара (oil, gas, metals, grains)")
    quantity: float = Field(..., gt=0, description="Количество в тоннах")
    price: float = Field(..., gt=0, description="Цена за единицу")
    currency: str = Field(default="USD", regex="^[A-Z]{3}$")
    seller: str = Field(..., description="Продавец")
    buyer: str = Field(..., description="Покупатель")
    delivery_terms: str = Field(..., description="Условия доставки (FOB, CIF, etc)")
    payment_terms: str = Field(..., description="Условия оплаты")
    delivery_date: str = Field(..., description="Дата доставки ISO format")
    origin_port: str = Field(..., description="Порт отгрузки")
    destination_port: str = Field(..., description="Порт назначения")
    additional_terms: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MarketAnalysisRequest(BaseModel):
    """Запрос на анализ рынка"""
    commodity: str = Field(..., description="Тип товара")
    region: str = Field(..., description="Регион анализа")
    timeframe: str = Field(default="1M", regex="^(1D|1W|1M|3M|1Y)$")
    include_forecast: bool = Field(default=True)


class ShipmentRequest(BaseModel):
    """Запрос на организацию логистики"""
    trade_id: str = Field(..., description="ID сделки")
    cargo_type: str = Field(..., description="Тип груза")
    weight_tons: float = Field(..., gt=0)
    origin: str = Field(..., description="Точка отправления")
    destination: str = Field(..., description="Точка назначения")
    preferred_carriers: Optional[List[str]] = Field(default_factory=list)
    special_requirements: Optional[List[str]] = Field(default_factory=list)


class RiskAssessmentRequest(BaseModel):
    """Запрос на оценку рисков"""
    trade_params: TradeRequest
    include_mitigation: bool = Field(default=True)
    risk_tolerance: str = Field(default="medium", regex="^(low|medium|high)$")


# Хранилище активных сделок (в production использовать БД)
active_trades: Dict[str, Dict[str, Any]] = {}


@router.post("/trades/create")
async def create_trade(
    trade_request: TradeRequest,
    background_tasks: BackgroundTasks,
    user=Depends(auth_user_dependency)
) -> Dict[str, Any]:
    """Создание новой сделки с полной валидацией и проверкой рисков"""
    
    # Инициализация агентов
    executor = TRADING_AGENTS["trade_executor"]()
    risk_manager = TRADING_AGENTS["risk_manager"]()
    compliance = TRADING_AGENTS["compliance_agent"]()
    
    trade_params = trade_request.dict()
    
    # 1. Валидация параметров сделки
    validation = await executor.validate_trade(trade_params)
    if not validation["is_valid"]:
        raise HTTPException(status_code=400, detail=validation["errors"])
    
    # 2. Проверка соответствия
    compliance_check = await compliance.check_compliance(trade_params)
    if not compliance_check["is_compliant"]:
        raise HTTPException(
            status_code=403, 
            detail=f"Compliance violations: {compliance_check['violations']}"
        )
    
    # 3. Оценка рисков
    risk_assessment = await risk_manager.assess_trade_risk(trade_params)
    if risk_assessment["overall_risk"] == "high" and user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="High risk trade requires admin approval"
        )
    
    # 4. Исполнение сделки
    execution_result = await executor.execute_trade(trade_params)
    
    # 5. Сохранение в активные сделки
    trade_id = execution_result["trade_id"]
    active_trades[trade_id] = {
        **execution_result,
        "validation": validation,
        "compliance": compliance_check,
        "risk_assessment": risk_assessment,
        "user_id": user.get("user_id")
    }
    
    # 6. Фоновая задача для генерации документов
    background_tasks.add_task(
        generate_trade_documents,
        trade_id,
        compliance_check["required_documents"]
    )
    
    return {
        "trade_id": trade_id,
        "status": "created",
        "risk_level": risk_assessment["overall_risk"],
        "required_documents": compliance_check["required_documents"],
        "next_steps": [
            "Document generation in progress",
            "Logistics planning available",
            "Market monitoring activated"
        ]
    }


@router.get("/trades/{trade_id}")
async def get_trade_details(
    trade_id: str,
    user=Depends(auth_user_dependency)
) -> Dict[str, Any]:
    """Получение деталей сделки"""
    
    if trade_id not in active_trades:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    trade = active_trades[trade_id]
    
    # Проверка доступа
    if trade["user_id"] != user.get("user_id") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    return trade


@router.post("/market/analyze")
async def analyze_market(
    request: MarketAnalysisRequest,
    user=Depends(auth_user_dependency)
) -> Dict[str, Any]:
    """Анализ рыночных условий для товара"""
    
    analyst = TRADING_AGENTS["market_analyst"]()
    
    # Базовый анализ
    analysis = await analyst.analyze_market_conditions(
        request.commodity,
        request.region
    )
    
    # Прогноз если запрошен
    if request.include_forecast:
        forecast = await analyst.predict_price_movement(
            request.commodity,
            request.timeframe
        )
        analysis["forecast"] = forecast
    
    return {
        "analysis": analysis,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "confidence_level": "medium",
        "data_sources": ["market_feeds", "historical_data", "news_analysis"]
    }


@router.post("/logistics/plan")
async def plan_logistics(
    request: ShipmentRequest,
    user=Depends(auth_user_dependency)
) -> Dict[str, Any]:
    """Планирование логистики для сделки"""
    
    # Проверка существования сделки
    if request.trade_id not in active_trades:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    coordinator = TRADING_AGENTS["logistics_coordinator"]()
    
    cargo_details = {
        "type": request.cargo_type,
        "weight": request.weight_tons,
        "origin": request.origin,
        "destination": request.destination,
        "commodity": active_trades[request.trade_id]["details"]["commodity"]
    }
    
    shipment_plan = await coordinator.plan_shipment(
        request.trade_id,
        cargo_details
    )
    
    # Добавление плана в сделку
    active_trades[request.trade_id]["shipment_plan"] = shipment_plan
    
    return {
        "shipment_plan": shipment_plan,
        "status": "planned",
        "next_actions": [
            "Confirm carriers",
            "Book shipping slots",
            "Arrange insurance"
        ]
    }


@router.post("/risk/assess")
async def assess_risk(
    request: RiskAssessmentRequest,
    user=Depends(auth_user_dependency)
) -> Dict[str, Any]:
    """Детальная оценка рисков для потенциальной сделки"""
    
    risk_manager = TRADING_AGENTS["risk_manager"]()
    
    assessment = await risk_manager.assess_trade_risk(request.trade_params.dict())
    
    response = {
        "risk_assessment": assessment,
        "recommendations": []
    }
    
    # Добавление рекомендаций на основе уровня риска
    if assessment["overall_risk"] == "high":
        response["recommendations"] = [
            "Consider additional insurance",
            "Request letter of credit",
            "Split shipment into smaller batches",
            "Perform enhanced due diligence"
        ]
    elif assessment["overall_risk"] == "medium":
        response["recommendations"] = [
            "Standard insurance coverage",
            "Regular progress monitoring",
            "Confirm payment terms"
        ]
    
    if request.include_mitigation:
        response["mitigation_strategies"] = []
        for factor in assessment["risk_factors"]:
            response["mitigation_strategies"].extend(factor.get("mitigation", []))
    
    return response


@router.get("/trades/active")
async def list_active_trades(
    user=Depends(auth_user_dependency),
    commodity: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """Список активных сделок с фильтрацией"""
    
    filtered_trades = []
    
    for trade_id, trade in active_trades.items():
        # Фильтр по доступу
        if trade["user_id"] != user.get("user_id") and user.get("role") != "admin":
            continue
        
        # Фильтр по товару
        if commodity and trade["details"]["commodity"] != commodity:
            continue
        
        # Фильтр по статусу
        if status and trade["status"] != status:
            continue
        
        filtered_trades.append({
            "trade_id": trade_id,
            "commodity": trade["details"]["commodity"],
            "quantity": trade["details"]["quantity"],
            "value": trade["details"]["price"] * trade["details"]["quantity"],
            "status": trade["status"],
            "risk_level": trade["risk_assessment"]["overall_risk"],
            "created_at": trade["timestamp"]
        })
    
    return {
        "total": len(filtered_trades),
        "trades": filtered_trades,
        "filters_applied": {
            "commodity": commodity,
            "status": status
        }
    }


@router.post("/documents/generate/{trade_id}")
async def generate_documents(
    trade_id: str,
    doc_type: str,
    user=Depends(auth_user_dependency)
) -> Dict[str, Any]:
    """Генерация торговых документов"""
    
    if trade_id not in active_trades:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    compliance = TRADING_AGENTS["compliance_agent"]()
    
    document = await compliance.generate_documents(trade_id, doc_type)
    
    return {
        "document": document,
        "download_url": f"/api/v1/trading/documents/{trade_id}/{doc_type}",
        "expires_in": "24h"
    }


# Вспомогательные функции
async def generate_trade_documents(trade_id: str, doc_types: List[str]):
    """Фоновая генерация документов для сделки"""
    compliance = TRADING_AGENTS["compliance_agent"]()
    
    for doc_type in doc_types:
        await compliance.generate_documents(trade_id, doc_type)
        # Сохранение в БД или файловой системе


# WebSocket для real-time обновлений
from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/ws/trades")
async def trade_updates_websocket(websocket: WebSocket):
    """WebSocket для получения обновлений по сделкам в реальном времени"""
    await websocket.accept()
    
    try:
        while True:
            # Ожидание сообщений от клиента
            data = await websocket.receive_json()
            
            if data.get("action") == "subscribe":
                trade_id = data.get("trade_id")
                # Подписка на обновления сделки
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "trade_id": trade_id
                })
            
            # Здесь будет логика отправки обновлений
            
    except WebSocketDisconnect:
        pass