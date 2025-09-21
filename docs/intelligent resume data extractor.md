
-----

### **intelligent resume data extractor**

**[Role & Goal]**

Act as a world-class Chief Dev Engineer and Solutions Architect. Your expertise lies in creating sophisticated, AI-powered knowledge engineering systems that utilize a **human-in-the-loop** approach. Your primary objective is to design a definitive plan for an intelligent system that:

1.  Parses multiple resume versions to build a structured **Master Career Database**.
2.  **Interactively interviews** me to elicit transversal skills, personal projects, motivations, and aspirations that are not present in the formal documents.
3.  Integrates all collected data into a single, holistic knowledge base, ready to power a downstream Generative AI agent for crafting world-class, authentic, and highly personalized career narratives.

**[Context & Problem Statement]**

I have multiple resume versions (PDF, DOCX) that represent my formal work history. However, this is an incomplete picture. A significant portion of my skills, passions, and potential is demonstrated through personal projects, open-source contributions, and self-directed learning. My career aspirations and core professional values are also not captured. My goal is to create a system that first consolidates my formal experience and then actively helps me articulate and structure this "hidden" information. The final, enriched database must enable an AI agent to build resumes and cover letters that are not only technically optimized but also deeply authentic and aligned with my personal and professional goals.

**[Core Task: Design & Implementation Plan]**

Develop a detailed plan for the Python-based system. Your response must address the following sections with precision, explicitly referencing the strategic goals from the playbook and the new interactive requirements.

**1. High-Level Architectural Design:**

  - Propose a multi-stage pipeline. For example: `Ingestion & OCR -> Normalization -> Core Information Extraction -> Accomplishment Deconstruction & Linking -> Strategic Consolidation -> **Interactive Enrichment & Elicitation** -> Final Database Generation`.
  - Describe the purpose of each stage, paying special attention to the new "Interactive Enrichment" phase.

**2. Recommended Technology Stack:**

  - List and justify the Python libraries for parsing and NLP. Also, suggest a simple framework for the interactive command-line interface (e.g., `questionary` or `Typer`) to facilitate a user-friendly Q\&A session.

**3. Strategic Master Career Database Schema:**

  - Define a comprehensive JSON schema that models the relationships between skills, experiences, and their impact. The schema must be expanded to include the interactively elicited data.
  - The schema must include the following keys and nested structures:
      - **`work_experience` & `projects`**: As defined previously, with the structured `accomplishments` object (`deconstructed`, `metrics`, `associated_skills`, `impact_score`).
      - **`skills_inventory`**: As defined previously, with skills linking to evidence pointers.
      - **`strategic_metadata`**: As defined previously (`job_title_variations`, `top_anchor_accomplishments`, `core_competencies`).
      - **`holistic_profile` (NEW)**: A top-level key to store the interactively collected data.
        ```json
        "holistic_profile": {
          "transversal_projects": [
            {
              "name": "Personal Render Farm Automation",
              "description": "Built a Python and Ansible-based system to manage and schedule render jobs across multiple personal machines, reducing manual oversight by 90%.",
              "skills_demonstrated": ["Python", "Ansible", "System Administration", "Process Automation"],
              "link": "https://github.com/my-repo/render-farm"
            }
          ],
          "professional_aspirations": {
            "target_roles": ["Generative AI Process Engineer", "Technical Director"],
            "industries_of_interest": ["VFX", "Game Development", "AI Research"],
            "technologies_to_learn": ["Advanced MLOps", "CUDA Programming"]
          },
          "core_motivators": ["Solving complex pipeline inefficiencies", "Mentoring junior artists and engineers", "Bridging the gap between creative and technical teams"],
          "personal_qualities": [
            {
              "trait": "Resilience",
              "evidence": "Pivoted a failing project by redesigning the core architecture mid-development, which ultimately led to a successful on-time launch."
            }
          ]
        }
        ```

**4. Implementation Strategy & Logic:**

  - **Accomplishment Deconstruction, Skill Linking, Impact Scoring, Data Consolidation:** Describe these as in the previous prompt.
  - **Interactive Elicitation Logic (NEW):** This is a critical new section.
      - **Triggering:** Explain that this module runs *after* the initial database is built. It should analyze the parsed data to identify potential gaps.
      - **Question Generation Strategy:** Describe how the system will generate targeted questions. For example:
          - *To find transversal projects:* "I see you have strong skills in 'Python' and 'Automation'. Have you worked on any personal projects, open-source tools, or hobbyist activities where you've used these skills? Please describe one."
          - *To identify personal qualities:* "Thinking about the project at 'Company XYZ', which you described as very challenging, what personal quality—like creativity, perseverance, or leadership—was most essential to your success there? Can you give an example?"
          - *To clarify aspirations:* "Your experience points towards expertise in process engineering. Looking forward, what kind of problems are you most excited to solve in your next role? What would be your ideal job title?"

**5. Proof-of-Concept Code:**

  - Provide two concise Python code snippets:
    1.  The **Accomplishment Deconstruction** function, as requested previously.
    2.  A new function demonstrating the **Interactive Elicitation** logic. It should take the partially built database as input, formulate one strategic question based on the data, and show how the user's answer would be structured for insertion into the `holistic_profile`.

**[Constraints]**

  - **Input:** Handle both a directory of files (`.pdf`, `.docx`) and interactive user input from the command line.
  - **Output:** A single, enriched, and validated JSON file adhering strictly to the final strategic schema.
  - **Strategic Alignment:** The entire design must be justified as the ultimate foundation for an AI agent tasked with building deeply personalized and effective career assets.
