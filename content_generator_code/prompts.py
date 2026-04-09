def expert_curriculam_prompt(topic:str, total_study_days: int, research_notes: str):
    return f"""
    You are an expert curriculum designer. The user wants to learn about '{topic}'
    
    
    Here is the researched syllabus outline and structural guidance:
    <research>
    {research_notes}
    </research>

    I need a progressive daily syllabus based on the research provided above

    CRITICAL INSTRUCTION: You must generate EXACTLY {total_study_days} daily sub-topics.
    Not one more, not one less. Move from beginner concepts to advanced concepts
    """

def researcher_prompt(topic: str, duration_months: int, web_context: str):
    return f"""
    You are an expert curriculum researcher and educational designer.
    The user wants to learn about {topic} over a period of {duration_months} months.

    Here is the latest websearch and live course structures fetched for this topic:
    <web_research>
    {web_context}
    </web_research>

    Your task is to outline a comprehensive, progressive syllabus for this topic. 
    Break it down into logical modules from beginner to advanced

    CRITICAL: You MUST incorporate the latest industry trends, modern frameworks, and advanced "burning topics" found in the web research provided above

    Provide detailed subtopics, key concepts, and best practices. 
    This outline will be used by a schedule architect to build a daily study plan. 
    Output a detailed, structured text outline. 
"""
