# Topic_to_Content
Give your Topic and the Agent shall provide you in-depth study material

High Level Plans:
    - User Gives any Topic of choice
    - User is Provided Subtopics of the topics
    - Each Subtopics consists of detailed explaination of the concepts including analogies
    - The subtopics also contains 10 questions that were taught in the section to test the user if they have learnt properly

Graph:
        [ START ]
           |
           v
+-------------------------+
|    Input_Processor      | 
+------------+------------+
             |
             v
+------------+------------+
|   Schedule_Architect    |
+------------+------------+
             |
             v
+------------+------------+
| Daily_Content_Generator | <-----------+ (Entry for next day)
+------------+------------+             |
             |                          |
             v                          |
+------------+------------+             |
|  Code_Presence_Checker  |             | (Router Node)
+------------+------------+             |
      /              \                  |
 (Has Code)      (No Code)              |
     |                |                 |
     v                |                 |
+------------+        |                 |
|Code_Syntax_|        |                 | (Agent 1: Skippable)
|  Checker   |        |                 |
+-----+------+        |                 |
      |               |                 |
      v               v                 |
+------------+------------+             |
|  Pedagogical_Validator  |             | (Agent 2: Always Runs)
+------------+------------+             |
             |                          |
      [ Is Content Valid? ]             |
      /                 \               |
   (FAIL)              (PASS)           |
     |                   |              |
     v                   v              |
+------------+    +--------------+      |
|  Refiner   |    |  State_Save  |      |
+------------+    +------+-------+      |
     |                   |              |
     +-------------------+--------------+
                         |
                [ Timeline Finished? ]
                 /                \
              (NO)               (YES)
               |                   |
               v                   v
      (Next Iteration)         [ END ]

