import asyncio
from datetime import date
from langgraph.graph import StateGraph, START, END

# Import the state and nodes from head.py
from head import (
    GraphState, 
    input_processor, 
    curriculum_researcher, 
    schedule_architect,
    daily_content_researcher,
    daily_content_generator,
    code_presence_checker,
    code_syntax_checker,
    route_after_code_check,
    state_save 
)

# ==========================================
# 1. LOOP MANAGEMENT (NEW)
# ==========================================

async def loop_incrementer(state: GraphState):
    """
    Increments the day counter and resets the daily variables 
    so the next iteration of the loop starts fresh.
    """
    print(f"\n--- [LOOPING] MOVING TO DAY {state.day_number + 1} ---")
    return {
        "day_number": state.day_number + 1,
        "current_topic": None,        # Reset so researcher finds the next topic
        "daily_web_context": None,    # Clear old web context
        "latest_content": None,       # Clear old lesson text
        "has_code": False             # Reset code detection
    }

def loop_router(state: GraphState):
    """
    Checks if we have reached our 5-day limit.
    If yes -> END. If no -> loop back to the researcher.
    """
    # We check > 5 because we want Day 5 to fully complete its save process first.
    if state.day_number > 5 or state.day_number > state.total_study_days:
        return END
    return "daily_content_researcher"


# ==========================================
# 2. GRAPH CONSTRUCTION
# ==========================================

workflow = StateGraph(GraphState)

# Add all the nodes
workflow.add_node("input_processor", input_processor)
workflow.add_node("curriculum_researcher", curriculum_researcher) 
workflow.add_node("schedule_architect", schedule_architect)
workflow.add_node("daily_content_researcher", daily_content_researcher)
workflow.add_node("daily_content_generator", daily_content_generator)
workflow.add_node("code_presence_checker", code_presence_checker)
workflow.add_node("code_syntax_checker", code_syntax_checker)
workflow.add_node("state_save", state_save) 
workflow.add_node("loop_incrementer", loop_incrementer) # <-- Added Incrementer Node

# Define the standard linear edges
workflow.add_edge(START, "input_processor")
workflow.add_edge("input_processor", "curriculum_researcher")
workflow.add_edge("curriculum_researcher", "schedule_architect")

# Enter the daily loop for Day 1
workflow.add_edge("schedule_architect", "daily_content_researcher") 
workflow.add_edge("daily_content_researcher", "daily_content_generator")
workflow.add_edge("daily_content_generator", "code_presence_checker")

# Code QA Routing
workflow.add_conditional_edges(
    "code_presence_checker",
    route_after_code_check,
    {
        "code_syntax_checker": "code_syntax_checker",
        "pedagogical_validator": "state_save"  # Still bypassing validator temporarily
    }
)

# Connect both QA paths to the save node
workflow.add_edge("code_syntax_checker", "state_save")

# AFTER saving, go to the incrementer instead of END
workflow.add_edge("state_save", "loop_incrementer")

# The final loop condition! Back to the top of the loop or END.
workflow.add_conditional_edges(
    "loop_incrementer",
    loop_router,
    {
        "daily_content_researcher": "daily_content_researcher",
        END: END
    }
)

# Compile the application
app = workflow.compile()

# ==========================================
# 3. ASYNC TEST RUNNER
# ==========================================

async def run_test():
    print("\n" + "="*50)
    print("🚀 STARTING LANGGRAPH 5-DAY LOOP TEST")
    print("="*50 + "\n")
    
    # Highly technical advanced engineering query!
    initial_input = {
        "topic": "MCP servers and Integration with Langgraph and Fast API", 
        "duration_months": 1, 
        "off_days": ["sunday", "SATURDAY"], 
        "start_date": date.today() 
    }
    
    try:
        final_state = await app.ainvoke(initial_input)
        
        print("\n" + "="*50)
        print("✅ 5-DAY TEST COMPLETED SUCCESSFULLY")
        print("="*50)
        
        filename = f"{initial_input['topic'].replace(' ', '_')}_Course.txt"
        print(f"\n[SUCCESS] The first 5 lessons have been sequentially written to: {filename}")
        
    except Exception as e:
        print(f"\n❌ ERROR DURING EXECUTION: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())