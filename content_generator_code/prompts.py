def expert_curriculam_prompt(topic:str, total_study_days: int):
    return f"""
    You are an expert curriculum designer. The user wants to learn about '{topic}'
    I need a progressive daily syllabus.

    CRITICAL INSTRUCTION: You must generate EXACTLY {total_study_days} daily sub-topics.
    Not one more, not one less. Move from beginner concepts to advanced concepts
    """
