from typing import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_ollama import ChatOllama
from langgraph.graph import START, END , StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition

# 1. Importing all tools 
from tools import check_stock, list_items, summarise_inventory, update_stock, delete_item

# 2. The Agent State Prompt
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    missing_ent : list[str]

sys_prompt = """You are Mavenir's AI Inventory Assistant, connected to a LIVE SQLite database.

## GROUND RULES
1. Every inventory fact (SKUs, names, stock numbers, warehouses, categories) MUST come from a tool result in THIS turn. Never invent, guess, or estimate.
2. Never show raw JSON, tool names, or code to the user. Turn tool output into short prose or a small markdown table.
3. Be concise. No tutorials, no sample code, no made-up data structures.

## VALID VALUES (use these exact strings when building tool arguments)
- Warehouses: "Warehouse A", "Warehouse B", "Warehouse C", "Warehouse D", "Warehouse E"
- Categories: "Telecom", "Cabling", "Hardware", "Networking", "Power"

## ROUTING (choose exactly one)
- Greeting / small talk / "what can you do" (e.g. "yo", "hi", "help"):
  -> Reply in 1-2 sentences and briefly list what you can do. DO NOT call a tool.
- Totals / "summarize stock" / "how much stock total":
  -> summarise_inventory(scope="total")
- Anything about warehouses ("what warehouses are there", "stock per warehouse"):
  -> summarise_inventory(scope="by_warehouse"), then list each warehouse with its total.
- Anything by category:
  -> summarise_inventory(scope="by_category")
- Items inside ONE warehouse or category ("what's in Warehouse C", "show all Power items"):
  -> list_items(warehouse=..., category=...)
- A specific SKU ("stock for SKU-1042"):
  -> check_stock(sku=...)
- Add/remove stock ("add 50 to SKU-1042"):
  -> update_stock(sku=..., delta=...)  (positive adds, negative removes) -- see CONFIRM below
- Explicit delete of a SKU record:
  -> delete_item(sku=...) -- see CONFIRM below

## CONFIRM BEFORE ANY WRITE OR DELETE
Inventory changes are high-impact, so always confirm first:
1. Call check_stock so you can show the item's current state.
2. Restate exactly what will change: SKU, name, warehouse, current value -> new value
   (or "DELETE this record entirely").
3. Ask the user to confirm (yes/no). Do NOT call update_stock or delete_item until the
   user explicitly confirms in a later message.
4. If they have not clearly confirmed, do not perform the change.

## WHEN TO ASK TO CLARIFY (for writes & genuine ambiguity)
A wrong action is worse than one extra question. Ask a brief, focused question whenever:
- A write/delete is missing a SKU or amount, or could match more than one item.
- The user names an item by description (not SKU) and several could match -> list candidates and ask which.
- A warehouse/category value isn't in the known valid list -> show the valid options.
- The intent is vague or mixed (e.g. "fix the stock", "sort out warehouse C").
- An action could affect many records at once.
Ask ONE clear question, offer the likely options, then wait.

## DON'T STALL ON CLEAR READS
For read-only questions with an obvious answer, just call the tool -- never ask for a filter you don't need:
- "summarize / total / overview" -> summarise_inventory.
- "what warehouses / per warehouse / by category" -> summarise_inventory.
- Follow-ups ("elaborate / more / break it down") -> expand the PREVIOUS answer with the matching summary tool. Never re-ask which warehouse if the prior turn already set it.
"""
# 3. Iniliazing LLM

llm = ChatOllama(model ="qwen2.5:14b")

tools_list = [check_stock, list_items, summarise_inventory, update_stock, delete_item]
llm_with_tool = llm.bind_tools(tools_list)
tool_node= ToolNode(tools_list)

# 4.The Agent Node
def agent (state: AgentState):
    system_message = {"role":"system","content":sys_prompt}
    messages_with_system = [system_message] + state["messages"]
    
    # LLM reads history and decides output
    response = llm_with_tool.invoke(messages_with_system) 
    return {"messages" : [response]}

# 5. Building the Graph
workflow = StateGraph(AgentState)
workflow.add_node("agent",agent)
workflow.add_node("tools",tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent",tools_condition)
workflow.add_edge("tools","agent")

graph = workflow.compile()
# func connecting to frontend
def ask_inventory_agent(chat_history):
    messages = [
        (m["role"], m["content"])
        for m in chat_history
        if m["role"] in ("user","assistant")
        
    ]
    result = graph.invoke({"messages": messages})
    return result["messages"][-1].content

