from typing import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_ollama import ChatOllama
from tools import check_stock
from langgraph.graph import START, END , StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition



class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    missing_ent : list[str]

sys_prompt = """You are an AI Inventory Management Assistant. Your strictly enforced role is READ-ONLY.

### CORE WORKFLOW
1. You MUST use the provided tools (`check_stock`, `list_items`, `summarise_inventory`) to fetch real data. Never make up inventory numbers.
2. If a user asks to check stock, use `check_stock`.
3. If a user asks for a broad overview, use `summarise_inventory` and adhere strictly to the allowed scope parameters (e.g., "all", "by_warehouse").

### HANDLING AMBIGUITY
- If a user's query is at all ambiguous (e.g., missing a specific SKU or warehouse), you must NOT guess.
- Instead of calling a tool, output a standard conversational reply asking the user to clarify. 

"""
llm = ChatOllama(model ="llama3.1")

tool = [check_stock]

llm_with_tool = llm.bind_tools(tool)

tool_node= ToolNode(tool)

def agent (state):
    system_message = {"role":"system","content":sys_prompt}
    messages_with_system = [system_message] + state["messages"]
    response = llm_with_tool.invoke(messages_with_system) 
    return {"messages" : [response]}

workflow = StateGraph(AgentState)
workflow.add_node("agent",agent)
workflow.add_node("tools",tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent",tools_condition)
workflow.add_edge("tools","agent")

graph = workflow.compile()
def ask_inventory_agent(user_input):
    initial_state = {"messages":[("user",user_input)]}
    result = graph.invoke(initial_state)
    return result["messages"][-1].content
