import asyncio
from datetime import date
from langgraph.graph import StateGraph, START, END

# Import the state and all nodes from head.py
from head import (
    GraphState, 
    input_processor, 
    curriculum_researcher, 
    schedule_architect,
    daily_content_researcher,
    daily_content_generator,
    code_presence_checker,
    code_syntax_checker,
    pedagogical_validator,
    refiner,
    refresher_generator,
    route_after_code_check,
    state_save 
)

# ==========================================
# 1. LOOP MANAGEMENT & ROUTERS
# ==========================================

async def loop_incrementer(state: GraphState):
    """
    Increments the day counter and resets the daily variables 
    so the next iteration of the loop starts fresh.
    """
    print(f"\n--- [LOOPING] MOVING TO DAY {state.day_number + 1} ---")
    return {
        "day_number": state.day_number + 1,
        "current_topic": None,        
        "daily_web_context": None,    
        "latest_content": None,       
        "has_code": False,
        "is_valid": False,
        "error_feedback": None,
        "refresher_questions": None
    }

def loop_router(state: GraphState):
    """
    Checks if we have reached our 5-day limit or total study days limit.
    """
    if state.day_number > 3 or state.day_number > state.total_study_days:
        return END
    return "daily_content_researcher"

def check_pedagogical_validity(state: GraphState):
    """
    Checks the verdict from the Editor-in-Chief.
    """
    if state.is_valid: 
        return "PASS"
    return "FAIL"

# ==========================================
# 2. GRAPH CONSTRUCTION
# ==========================================

workflow = StateGraph(GraphState)

# Add all the nodes to the graph
workflow.add_node("input_processor", input_processor)
workflow.add_node("curriculum_researcher", curriculum_researcher) 
workflow.add_node("schedule_architect", schedule_architect)
workflow.add_node("daily_content_researcher", daily_content_researcher)
workflow.add_node("daily_content_generator", daily_content_generator)
workflow.add_node("code_presence_checker", code_presence_checker)
workflow.add_node("code_syntax_checker", code_syntax_checker)
workflow.add_node("pedagogical_validator", pedagogical_validator) 
workflow.add_node("refiner", refiner)                               
workflow.add_node("refresher_generator", refresher_generator)       
workflow.add_node("state_save", state_save) 
workflow.add_node("loop_incrementer", loop_incrementer)

# Phase 1: Planning
workflow.add_edge(START, "input_processor")
workflow.add_edge("input_processor", "curriculum_researcher")
workflow.add_edge("curriculum_researcher", "schedule_architect")

# Phase 2: Daily Generation Loop Entry
workflow.add_edge("schedule_architect", "daily_content_researcher") 
workflow.add_edge("daily_content_researcher", "daily_content_generator")
workflow.add_edge("daily_content_generator", "code_presence_checker")

# Phase 3: Technical QA Routing
workflow.add_conditional_edges(
    "code_presence_checker",
    route_after_code_check,
    {
        "code_syntax_checker": "code_syntax_checker",
        "pedagogical_validator": "pedagogical_validator" 
    }
)
workflow.add_edge("code_syntax_checker", "pedagogical_validator")

# Phase 4: Pedagogical QA & The Self-Correcting Loop
workflow.add_conditional_edges(
    "pedagogical_validator",
    check_pedagogical_validity,
    {
        "PASS": "refresher_generator",  # If valid, generate the quiz!
        "FAIL": "refiner"               # If invalid, rewrite it!
    }
)
# The crucial loop-back edge! Ensures rewritten text gets code-checked again
workflow.add_edge("refiner", "code_presence_checker")

# Phase 5: Saving & Iterating
workflow.add_edge("refresher_generator", "state_save")
workflow.add_edge("state_save", "loop_incrementer")

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
    print("🚀 STARTING LANGGRAPH FULL PIPELINE LOOP TEST")
    print("="*50 + "\n")
    
    initial_input = {
        "topic": "Generative AI with MCP, Langgraph and Fast API", 
        "duration_months": 1.5, 
        "off_days": ["sunday", "SATURDAY"], 
        "start_date": date.today() 
    }
    
    try:
        final_state = await app.ainvoke(initial_input)
        
        print("\n" + "="*50)
        print("✅ FULL 5-DAY TEST COMPLETED SUCCESSFULLY")
        print("="*50)
        
        # Format updated to explicitly reflect .md
        filename = f"{initial_input['topic'].replace(' ', '_')}_Course.md"
        print(f"\n[SUCCESS] The lessons and quizzes have been perfectly written to: {filename}")
        
    except Exception as e:
        print(f"\n❌ ERROR DURING EXECUTION: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())