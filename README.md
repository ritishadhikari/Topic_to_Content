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
    