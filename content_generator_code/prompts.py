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

def daily_content_prompt(course_topic: str, daily_topic: str, web_context: str):
    return f"""
    You are an expert technical instructor teaching a course on {course_topic}
    Your task is to write a comprehensive, engaging daily lesson for today's specific sub-topic: {daily_topic}

    Here is the latest web research, documentation and technical context gathered for this specific topic:
    <web_research>
    {web_context}
    </web_research>

    Instructions:
    1. Write a clear, beginner-friendly introduction to the concept
    2. Explain the core mechanics using the web search provided 
    3. Include practical examples, analogies and strictly accurate code snippets (if applicable)
    4. Keep the tone encouraging and highly educational
    5. Do not write a generic summary; write an actual, deep-dive textbook-style lesson.
    """

def code_presence_checker_prompt(content: str):
    return f"""
    Does the following lesson content contain any executable code blocks, CLI commands, or programming syntax?
    {content}
    """

def syntax_checker_prompt(latest_content: str, course_topic: str, daily_topic: str ):
    return f"""
    You are an expert Senior Software Engineer and Code Reviewer.
    Review the following educational lesson for the course {course_topic} specially focussing on the sub-topic {daily_topic}
    It contains code snippets

    <lesson>
    {latest_content}
    </lesson>

    Your Tasks:
    1. Check every code block for syntax error, deprecations, or bad practices.
    2. Ensure the code is highly relevant to {daily_topic} and perfectly matches the explanations given in the text.
    3. If the code is perfect and contextually accurate, set 'is_valid' to True and return the original text.
    4. If there are syntax errors OR if the code is irrelevant/out-of-scope for the topic, fix it, set 'is_valid' to False and output the fully corrected lesson text.
    """

def pedagogical_validator_prompt(course_topic: str, daily_topic: str, lesson_content: str, web_context: str):
    return f"""
    You are an Expert Editor-in-Chief and Master Teacher.
    Review the following technical lesson for the course: {course_topic}, specifically focussing on {daily_topic}

    <lesson>
    {lesson_content}
    </lesson>

    <source_of_truth>
    {web_context}
    </source_of_truth>

    Your criteria for validation:
    1. Comprehension: Is the content extremely easy to grasp for an intermediate learner?
    2. Analogies: Does the lesson use strong, relatable, real-world analogies? (Ensure analogies do not contradict the source of truth)
    3. Cognitive Load: Are paragraphs short and digestible? Is dense jargon explained clearly?
    4. Technical Accuracy: You MUST NOT hallucinate. Any rewrites or additions must perfectly allign with the <source_of_truth> provided above
    5. Engagement: Is the tone encouraging and conversational?

    If the lesson meets all these criteria perfectly, set 'is_pedagogically_sound' to True and return the original text

    If it falls short, rewrite and polidh the lesson, set 'is_pedagogically_sound' to False. provide brief feedback on what you have changed, and output the 'revised_content'
    """ 