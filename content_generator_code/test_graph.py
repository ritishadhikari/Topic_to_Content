import asyncio
from datetime import date
from langgraph.graph import StateGraph, START, END

# Import the state and our two nodes from your head.py file
from head import GraphState, input_processor, schedule_architect

# ==========================================
# 1. GRAPH CONSTRUCTION
# ==========================================

# Initialize the StateGraph with our Pydantic BaseModel
workflow = StateGraph(GraphState)

# Add our two completed nodes
workflow.add_node("input_processor", input_processor)
workflow.add_node("schedule_architect", schedule_architect)

# Define the flow (Edges)
workflow.add_edge(START, "input_processor")
workflow.add_edge("input_processor", "schedule_architect")

# For now, we point the Architect directly to END to test the planning phase
workflow.add_edge("schedule_architect", END) 

# Compile the application
app = workflow.compile()

# ==========================================
# 2. ASYNC TEST RUNNER
# ==========================================

async def run_test():
    print("\n" + "="*50)
    print("🚀 STARTING LANGGRAPH CHECKPOINT TEST")
    print("="*50 + "\n")
    
    # Simulate a user requesting a 1-month Python course starting today
    initial_input = {
        "topic": "Python Programming for Beginners",
        "duration_months": 1, # Keep it to 1 month for a faster test run
        "off_days": ["sunday", "SATURDAY"], # Testing your capitalization sanitizer!
        "start_date": date.today() 
    }
    
    try:
        # Execute the graph asynchronously 
        final_state = await app.ainvoke(initial_input)
        
        print("\n" + "="*50)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("="*50)
        
        # Verify the State Outputs
        print(f"\n[STATE CHECK] First Target Date: {final_state['current_target_date']}")
        print(f"[STATE CHECK] Total Calendar Days Generated: {len(final_state['full_schedule'])}")
        
        print("\n[PREVIEW] First 5 Days of the Master Schedule:")
        for day in final_state['full_schedule'][:5]:
            # Formatting the output nicely
            day_str = f"Date: {day['date']} | Type: {day['type']:<9} | "
            if day['type'] == 'STUDY_DAY':
                day_str += f"Day #{day['day_number']:<2} | Topic: {day['topic_metadata']}"
            else:
                day_str += f"Day: {day['day_name']}"
            print(day_str)
            
    except Exception as e:
        print(f"\n❌ ERROR DURING EXECUTION: {e}")

# Run the async event loop
if __name__ == "__main__":
    asyncio.run(run_test())