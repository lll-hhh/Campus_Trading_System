"""
AI聊天助手路由
支持商品分析、冲突解决等功能
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import httpx
from sqlalchemy.orm import Session

from apps.core.config import get_settings
from apps.api_gateway.dependencies import get_db_session, get_current_user
from apps.core.models import User

router = APIRouter(prefix="/ai", tags=["AI助手"])

settings = get_settings()


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str  # user, assistant, system
    content: str


class ChatRequest(BaseModel):
    """聊天请求"""
    messages: List[ChatMessage]
    context_type: str | None = None  # item_analysis, conflict_resolution, general
    context_data: dict | None = None  # 额外的上下文数据


class ChatResponse(BaseModel):
    """聊天响应"""
    message: str
    finish_reason: str | None = None


def build_system_prompt(context_type: str | None, context_data: dict | None) -> str:
    """构建系统提示词"""
    base_prompt = """你是CampusSwap校园二手交易平台的AI助手。你的职责是：
1. 帮助用户分析商品信息，给出合理的价格建议和交易建议
2. 协助解决交易冲突，提供公正的仲裁建议
3. 回答用户关于平台使用的问题
4. 保持友好、专业的态度

请用简洁明了的中文回答，每次回复控制在200字以内。"""

    if context_type == "item_analysis" and context_data:
        item_info = f"""
当前分析商品：
- 标题：{context_data.get('title', '未知')}
- 价格：¥{context_data.get('price', 0)}
- 描述：{context_data.get('description', '无')}
- 类别：{context_data.get('category', '未知')}
- 状况：{context_data.get('condition', '未知')}

请基于以上信息提供分析和建议。"""
        return base_prompt + item_info

    elif context_type == "conflict_resolution" and context_data:
        conflict_info = f"""
当前冲突案例：
- 类型：{context_data.get('conflict_type', '未知')}
- 买家观点：{context_data.get('buyer_view', '未提供')}
- 卖家观点：{context_data.get('seller_view', '未提供')}
- 交易金额：¥{context_data.get('amount', 0)}

请提供公正的解决建议。"""
        return base_prompt + conflict_info

    return base_prompt


async def call_glm_api(messages: List[dict]) -> str:
    """调用GLM API"""
    if not settings.glm_api_key:
        raise HTTPException(status_code=500, detail="GLM API密钥未配置")

    headers = {
        "Authorization": f"Bearer {settings.glm_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": settings.glm_model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.glm_api_base}/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                raise HTTPException(status_code=500, detail="AI响应格式错误")
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI服务响应超时")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"AI服务错误: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    与AI助手对话
    
    支持的context_type:
    - item_analysis: 商品分析
    - conflict_resolution: 冲突解决
    - general: 普通对话
    """
    try:
        # 构建系统提示词
        system_prompt = build_system_prompt(request.context_type, request.context_data)
        
        # 准备消息列表
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加历史消息（最多保留最近5轮对话）
        history = [{"role": msg.role, "content": msg.content} for msg in request.messages[-10:]]
        messages.extend(history)
        
        # 调用GLM API
        ai_response = await call_glm_api(messages)
        
        return ChatResponse(
            message=ai_response,
            finish_reason="stop"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求失败: {str(e)}")


@router.get("/health")
async def check_ai_health():
    """检查AI服务健康状态"""
    if not settings.glm_api_key:
        return {
            "status": "unavailable",
            "message": "GLM API密钥未配置"
        }
    
    try:
        # 发送测试消息
        test_messages = [
            {"role": "system", "content": "你是一个测试助手"},
            {"role": "user", "content": "hi"}
        ]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.glm_api_base}/chat/completions",
                json={
                    "model": settings.glm_model,
                    "messages": test_messages,
                    "max_tokens": 10
                },
                headers={
                    "Authorization": f"Bearer {settings.glm_api_key}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            
        return {
            "status": "healthy",
            "message": "AI服务正常",
            "model": settings.glm_model
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"AI服务异常: {str(e)}"
        }


class AnalyzeItemRequest(BaseModel):
    """商品分析请求"""
    item_id: int


@router.post("/quick-actions/analyze-item")
async def quick_analyze_item(
    request: AnalyzeItemRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """快速分析商品"""
    from apps.services.business_logic import ItemService
    
    # 获取商品信息
    item = ItemService.get_item_detail(session, request.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    # 准备上下文
    context_data = {
        "title": item.title,
        "price": float(item.price),
        "description": item.description or "",
        "category": item.category.name if item.category else "未分类",
        "condition": item.condition_type
    }
    
    # 构建分析请求
    system_prompt = build_system_prompt("item_analysis", context_data)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "请分析这个商品的价格合理性和交易建议"}
    ]
    
    ai_response = await call_glm_api(messages)
    
    return {
        "item_id": request.item_id,
        "analysis": ai_response
    }


@router.post("/quick-actions/resolve-conflict")
async def quick_resolve_conflict(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """快速生成冲突解决建议"""
    from apps.services.business_logic import TransactionService
    
    # 获取交易信息
    transaction = session.query(
        __import__('apps.core.models.transactions', fromlist=['Transaction']).Transaction
    ).filter_by(id=transaction_id).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="交易不存在")
    
    # 检查权限
    if transaction.buyer_id != current_user.id and transaction.seller_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权访问此交易")
    
    # 准备冲突上下文
    context_data = {
        "conflict_type": "交易纠纷",
        "buyer_view": "买家认为商品与描述不符",
        "seller_view": "卖家认为商品如实描述",
        "amount": float(transaction.final_amount)
    }
    
    system_prompt = build_system_prompt("conflict_resolution", context_data)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "请给出公正的解决建议"}
    ]
    
    ai_response = await call_glm_api(messages)
    
    return {
        "transaction_id": transaction_id,
        "suggestion": ai_response
    }
