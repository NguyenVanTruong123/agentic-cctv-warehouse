"""
Module graph.py:
Xay dung Do thi Trang thai LangGraph (StateGraph) theo mo hinh ReAct.
Tich hop co che Du phong (Fallback Mechanism):
  - Uu tien 1: Google Gemini (gemini-1.5-flash)
  - Du phong: DeepSeek (deepseek-chat qua OpenAI API compatible)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Dam bao import duoc package src
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Bat UTF-8 cho console Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load bien moi truong tu file .env
load_dotenv(PROJECT_ROOT / ".env")

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from src.agent.state import AgentState
from src.agent.tools import ALL_TOOLS
from src.agent.prompts import get_system_prompt


def build_llm_with_fallback():
    """
    Khoi tao LLM voi co che Du phong (Fallback) tu dong:
      - Uu tien 1: Google Gemini (gemini-2.5-flash)
      - Du phong (Fallback): DeepSeek (deepseek-chat qua OpenAI API format)
    Khi Gemini gap loi (het han quota, loi key 400/403, timeout 503, ...),
    he thong lap tuc tu dong chuyen sang goi DeepSeek Chat ma khong gay gian doan.
    """
    google_key = os.getenv("GOOGLE_API_KEY", "")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")

    # 1. Mo hinh chinh: Google Gemini (gemini-2.5-flash)
    primary_llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=google_key,
        temperature=0.1,
        max_retries=1
    )
    primary_with_tools = primary_llm.bind_tools(ALL_TOOLS)

    # 2. Mo hinh du phong: DeepSeek Chat (neu co key)
    if deepseek_key and deepseek_key.strip() != "your_deepseek_api_key_here":
        fallback_llm = ChatOpenAI(
            api_key=deepseek_key.strip(),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            model="deepseek-chat",
            temperature=0.1,
            max_retries=1
        )
        fallback_with_tools = fallback_llm.bind_tools(ALL_TOOLS)
        print("[INFO] Da kich hoat co che Du phong Fallback: Gemini -> DeepSeek")
        # Bat toan bo cac ngoai le tu Gemini (Exception) de tu dong chuyen sang DeepSeek
        return primary_with_tools.with_fallbacks([fallback_with_tools], exceptions_to_handle=(Exception,))

    return primary_with_tools


# Khoi tao model da gan san Tools va co che Fallback
llm_with_tools = build_llm_with_fallback()


def agent_node(state: AgentState):
    """Node Agent: LLM doc hoi thoai va quyet dinh tra loi hoac goi Tool."""
    active_cam = state.get("active_camera", None)
    system_prompt = get_system_prompt(active_camera=active_cam)

    # Chen System Message vao dau lich su tin nhan
    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState):
    """Ham dieu huong: Neu co tool_calls thi sang Node 'tools', nguoc lai ket thuc."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
        return "tools"
    return END


def create_agent_graph():
    """Xay dung va bien dich Do thi LangGraph."""
    workflow = StateGraph(AgentState)

    # 1. Them cac Node
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools=ALL_TOOLS))

    # 2. Them cac Canh noi luong
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    workflow.add_edge("tools", "agent")  # Vong lap quay lai agent sau khi tool chay xong

    # 3. Bien dich do thi
    app = workflow.compile()
    return app


# Khoi tao san ung dung do thi
agent_app = create_agent_graph()


def chat_with_agent(user_message: str, history: list = None, active_camera: str = "CAM-03"):
    """Ham giao tiep nhanh voi Agent tu code Python hoac API."""
    messages = list(history) if history else []
    messages.append(HumanMessage(content=user_message))

    initial_state = {
        "messages": messages,
        "active_camera": active_camera
    }

    # Gioi han recursion_limit = 6 de chong lap vo tan
    final_state = agent_app.invoke(initial_state, config={"recursion_limit": 6})
    final_reply = final_state["messages"][-1].content
    if isinstance(final_reply, list):
        final_reply = "".join(
            b.get("text", "") if isinstance(b, dict) else str(b)
            for b in final_reply
        )
    return final_reply, final_state["messages"]


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🤖 CHATBOT GIAM SAT AN TOAN NHA KHO (LANGGRAPH REACT AGENT)")
    print(" - Model chinh: Google Gemini (gemini-2.5-flash)")
    print(" - Co che Du phong: DeepSeek Chat (deepseek-chat)")
    print(" - Go 'exit' hoac 'quit' de thoat.")
    print("=" * 70 + "\n")

    chat_history = []
    default_camera = "CAM-03"

    while True:
        try:
            user_input = input("👤 Ban: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("👋 Tam biet anh!")
                break

            print("⏳ [AI dang suy luan & tra cuu Database...] ")
            reply, chat_history = chat_with_agent(
                user_message=user_input,
                history=chat_history,
                active_camera=default_camera
            )
            print(f"\n🤖 Agent:\n{reply}\n")
            print("-" * 70)

        except KeyboardInterrupt:
            print("\n👋 Da dung chuong trinh.")
            break
        except Exception as e:
            print(f"\n❌ [LOI HE THONG]: {e}\n")
