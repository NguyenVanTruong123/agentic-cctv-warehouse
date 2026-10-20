"""
Module state.py:
Dinh nghia cau truc trang thai hoi thoai (AgentState) cho LangGraph.
Su dung add_messages de tu dong cong don lich su hoi thoai giua User, Agent va Tools.
"""

from typing import Annotated, Sequence, Optional, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    # Danh sach tin nhan hoi thoai multi-turn (tu dong cong don)
    messages: Annotated[Sequence[BaseMessage], add_messages]
    # Ma camera nguoi dung dang mo xem tren web (neu co)
    active_camera: Optional[str]
