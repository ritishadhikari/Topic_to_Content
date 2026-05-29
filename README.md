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



                                        +-----------+                
                                        | __start__ |                             
                                        +-----------+                             
                                              *                                   
                                              *                                   
                                              *                                   
                                     +-----------------+                          
                                     | input_processor |                          
                                     +-----------------+                          
                                              *                                   
                                              *                                   
                                              *                                   
                                  +-----------------------+                       
                                  | curriculum_researcher |                       
                                  +-----------------------+                       
                                              *                                   
                                              *                                   
                                              *                                   
                                    +--------------------+                        
                                    | schedule_architect |                        
                                    +--------------------+                        
                                              *                                   
                                              *                                   
                                              *                                   
                                +--------------------------+                      
                                | daily_content_researcher |                      
                                +--------------------------+.                     
                                     ***                     ......               
                                  ***                              .....          
                                **                                      ......    
               +-------------------------+                                    ... 
               | daily_content_generator |                                      . 
               +-------------------------+                                      . 
                            *                                                   . 
                            *                                                   . 
                            *                                                   . 
                +-----------------------+                                       . 
                | code_presence_checker |                                       . 
                +-----------------------+                                       . 
                   ...              ...                                         . 
                ...                    ...                                      . 
              ..                          ...                                   . 
+---------------------+                      ..                                 . 
| code_syntax_checker |                   ...                                   . 
+---------------------+                ...                                      . 
                   ***              ...                                         . 
                      ***        ...                                            . 
                         **    ..                                               . 
                +-----------------------+                                       . 
                | pedagogical_validator |                                       . 
                +-----------------------+                                       . 
                            *                                                   . 
                            *                                                   . 
                            *                                                   . 
                 +---------------------+                                        . 
                 | refresher_generator |                                        . 
                 +---------------------+                                        . 
                            *                                                   . 
                            *                                                   . 
                            *                                                   . 
                    +----------------+                                          . 
                    | database_saver |                                          . 
                    +----------------+                                          . 
                            *                                                   . 
                            *                                                   . 
                            *                                                   . 
                    +---------------+                                         ... 
                    | state_updater |                                   ......    
                    +---------------+                              .....          
                                     ***                     ......               
                                        ***            ......                     
                                           **       ...                           
                                    +------------------+                          
                                    | loop_incrementer |                          
                                    +------------------+                          
                                              .                                   
                                              .                                   
                                              .                                   
                                         +---------+                              
                                         | __end__ |                              
                                         +---------+   


Folder Structures as of Now:

## 📂 Project Directory Structure

Topic_to_Content/
├── .github/
│   └── workflows/
│       └── ci-pipeline.yml
├── backend_code/
│   ├── content_generator_code/
│   │   ├── check_database.py
│   │   ├── course_content_pydantic_schemas.py
│   │   ├── head.py
│   │   ├── helper_functions.py
│   │   ├── pipeline_runner.py
│   │   ├── prompts.py
│   │   └── variables.py
│   ├── routers/
│   │   ├── authentication.py
│   │   └── course_generate.py
│   ├── api_pydantic_schemas.py
│   ├── database.py
│   └── security.py
├── demo_files/
│   └── mcp_crash_report.txt
├── mcp_code/
│   └── mcp_server.py
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_courses.py
│   ├── test_health.py
│   └── test_mcp.py
├── .dockerignore
├── .env
├── .gitignore
├── api.py
├── docker-compose.yaml
├── Dockerfile
├── Dockerfile.mcp
├── README.md
└── requirements.txt


Run MongoDB in the container: 

docker exec course_generator_db mongosh --eval "rs.initiate({_id:'rs0',members:[{_id:0, host:'mongodb:27017'}]})"