                [ START ]
                    |
                    v
          +-------------------------+
          |     Input_Processor     | <-- Sanitizes user inputs & sets defaults
          +------------+------------+
                    |
                    v
          +-----------------------+
          | Curriculum_Researcher | <-- Web search & syllabus synthesis
          +-----------+-----------+ 
                    | 
                    v
          +------------+------------+
          |   Schedule_Architect    | <-- Calendar math & Exact JSON generation
          +------------+------------+
                    |
                    v
          +------------+--------------+
    +---->|  Daily_Content_Researcher | 
    |     +------------+--------------+             
    |               |                               
    |               v                               
    |     +------------+------------+              
    |     | Daily_Content_Generator | 
    |     +------------+------------+         
    |               |                         
    |               v                         
    |     +------------+------------+         
    |     |  Code_Presence_Checker  |         
    |     +------------+------------+         
    |            /          \                 
    |      (Has Code)    (No Code)            
    |          |              |               
    |          v              |               
    |   +------------+        |  
    |   |Code_Syntax_|        |  
    |   |  Checker   |        |  
    |   +-----+------+        v  
    |         |               |               
    |         v               |               
    |   +------------+        |               
    |   | Pedagogical| <------+               
    |   |  Validator |                        
    |   +-----+------+                        
    |         |                               
    |                         
    |         |                                       
    |       
    |         |                                    
    |    +---------------------+
    |    | Refresher Generator | <-- 10 Questions Synth
    |    +----------+----------+
    |               |
    |               v
    |           +--------------+
    |           |  State_Save  |
    |           +------+-------+
    |               |
    |           [ Timeline Finished? ]
    |            /                 \
    |           (NO)               (YES)
    |              |                   |
    |              v                   v
    |       (Next Iteration)        [ END ]
    ---------------|                 
    

Folder Structures as of Now:

Topic_to_Content/
├── .github/
│   └── workflows/
│       └── ci-pipeline.yml
├── backend_code/
│   ├── __init__.py
│   ├── database.py
│   ├── pydantic_schema.py
│   ├── security.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── authentication.py
│   │   └── course_generate.py
│   └── content_generator_code/
│       ├── __init__.py
│       ├── head.py
│       ├── helper_functions.py
│       ├── pipeline_runner.py
│       ├── prompts.py
│       ├── pydantic_schemas.py
│       └── variables.py
├── .env
├── .gitignore
├── api.py
├── README.md
└── requirements.txt


Run MongoDB in the container: 

docker exec -it course_generator_db mongosh
    - rs.initiate()
    - use ai_course_generator
    - db.daily_lessons.countDocuments()
    - db.daily_lessons.find().sort({ generated_at: -1 }).limit(1).pretty()