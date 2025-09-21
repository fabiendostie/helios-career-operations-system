
-----

### **Knowledge Document 1/5: `PROFILE_INGESTOR`**

**ID:** `KDB-INGESTOR-2.1`
**Subject:** Advanced Conversational Profiling & Data Structuring
**Description:** This document provides the `PROFILE_INGESTOR` agent with the frameworks and protocols necessary to conduct a deep, empathetic, and forensically detailed Discovery Interview. The goal is to transcend simple data collection and achieve genuine user understanding.

**1.0 Core Psychological Frameworks**

The interview process is not random; it is guided by established models of career motivation and interest.

  * **1.1 Schein's Career Anchors Model:** Used to uncover a user's fundamental career drivers. The agent must probe for evidence of these 8 anchors:

    1.  `Technical/Functional Competence (TF)`: The user is driven by their expertise and the work itself.
    2.  `General Managerial Competence (GM)`: Driven by the opportunity to lead, manage, and be responsible for outcomes.
    3.  `Autonomy/Independence (AU)`: Driven by the freedom to define their own work.
    4.  `Security/Stability (SE)`: Driven by predictability and job security.
    5.  `Entrepreneurial Creativity (EC)`: Driven by the need to create something new.
    6.  `Service/Dedication to a Cause (SV)`: Driven by values and a desire to make a difference.
    7.  `Pure Challenge (CH)`: Driven by solving impossible problems.
    8.  `Lifestyle (LS)`: Driven by integrating work and personal life.

  * **1.2 Holland Codes (RIASEC Model):** Used to map a user's interests to work environments. The agent should listen for language that aligns with these 6 types:

    1.  `Realistic (R)`: "Do-ers" - Practical, physical, hands-on.
    2.  `Investigative (I)`: "Thinkers" - Analytical, intellectual, scientific.
    3.  `Artistic (A)`: "Creators" - Expressive, original, independent.
    4.  `Social (S)`: "Helpers" - Cooperative, supportive, nurturing.
    5.  `Enterprising (E)`: "Persuaders" - Competitive, leaders, ambitious.
    6.  `Conventional (C)`: "Organizers" - Detail-oriented, organized, clerical.

**2.0 The Funneling Interview Protocol**

The agent will follow a multi-stage questioning protocol designed to move from broad facts to deep motivations.

1.  **Stage 1: Factual Baseline (The "What"):** Ingest the raw resume. Extract key facts to establish context.
2.  **Stage 2: Behavioral Probing (The "How"):** Ask for specific, story-based examples using the STAR method (Situation, Task, Action, Result) as a guide. *Example Question: "Your resume says you 'led a project.' Can you walk me through that specific project? What was the situation, what were you tasked with, what specific actions did you take, and what was the measurable result?"*
3.  **Stage 3: Motivational Inquiry (The "Why"):** Connect accomplishments to feelings and drivers. *Example Question: "Thank you for that example. Of all the parts of that project, which part did you find the most energizing or satisfying? Was it solving the technical problem (TF), coordinating the team (GM), or something else?"*
4.  **Stage 4: Aspirational Exploration (The "What Next"):** Probe for future-state desires, informed by the uncovered anchors and interests. *Example Question: "Given your interest in [RIASEC Type] and your drive for [Career Anchor], what kind of problems do you hope to solve in your next role?"*

**3.0 Natural Language to Structured Data Mapping Schema**

This is the internal logic for converting conversational input into the structured YAML profile.

```json
{
  "mapping_rules": [
    {
      "input_keywords": ["lead", "manage team", "responsible for budget", "coordinate"],
      "target_field": "career_constraints.career_anchors",
      "value": "General Managerial Competence (GM)",
      "confidence_threshold": 0.7
    },
    {
      "input_keywords": ["analyze data", "research", "investigate", "run experiments", "sql", "python"],
      "target_field": "career_constraints.riasec_code",
      "value": "Investigative (I)",
      "confidence_threshold": 0.6
    },
    {
      "input_pattern": "Increased [METRIC] by [VALUE]%",
      "target_field": "professional_inventory.quantified_impact_achievements",
      "value_template": "Drove a ${VALUE}% increase in ${METRIC} by [inferred_action]."
    }
  ]
}
```

**4.0 Bias Mitigation Protocol**

To ensure data integrity, the agent must actively avoid common interviewing biases:

  * **Confirmation Bias:** Do not ask questions that merely confirm what's on the resume. Ask questions that challenge or seek new information.
  * **Leading Questions:** Do not ask, "Are you a good leader?" Instead, ask, "Tell me about a time you had to lead a project."
  * **Halo/Horn Effect:** Do not let one particularly good or bad answer color the entire interview. Treat each question section as a distinct data-gathering phase.

-----
