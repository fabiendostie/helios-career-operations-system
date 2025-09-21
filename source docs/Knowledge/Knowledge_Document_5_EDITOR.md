-----

### **Knowledge Document 5/5: `EDITOR`**

**ID:** `KDB-EDITOR-1.0`
**Subject:** Granular Text Optimization & Lexical Enhancement
**Description:** This document provides the `EDITOR` agent with the micro-frameworks and lexical databases required to perform high-precision optimizations on individual text snippets.

**1.0 Core Framework: The XYZ Quantification Model**

A more prescriptive version of STAR, designed for concise, powerful resume bullet points.
**`Accomplished [X] as measured by [Y] by doing [Z].`**

  * **`X` (The Accomplishment):** A high-impact result. *e.g., "Reduced server response time..."*
  * **`Y` (The Quantification):** The measurable metric. *e.g., "...by 300ms (a 40% improvement)..."*
  * **`Z` (The Method):** The action, skills, or tools used. *e.g., "...by refactoring the primary API endpoint and implementing a Redis caching layer."*

**2.0 Lexical Database**

  * **2.1 Weak Word Replacement Table:** The agent will perform a search-and-replace based on this table to eliminate passive or weak language.
    | Weak Phrase | Stronger Alternatives |
    | :--- | :--- |
    | Helped with / Assisted in | Supported, Facilitated, Contributed to, Enabled |
    | Responsible for | Owned, Managed, Governed, Oversaw |
    | Worked on | Developed, Executed, Implemented, Created, Led |
    | Was a member of a team that | Collaborated with a team to, Partnered with [X] engineers to |
    | Familiar with / Experience in | Proficient in, Expertise in, Applied, Utilized |

  * **2.2 High-Impact Verb Thesaurus (Categorized):** A database of powerful verbs categorized by function, allowing the agent to select the most appropriate word for the context.

    ```json
    {
      "category": "Management",
      "verbs": ["Orchestrated", "Coordinated", "Governed", "Scaled", "Mentored", "Spearheaded"]
    },
    {
      "category": "Technical",
      "verbs": ["Architected", "Engineered", "Automated", "Deployed", "Refactored", "Optimized"]
    },
    {
      "category": "Data & Analysis",
      "verbs": ["Quantified", "Modeled", "Forecasted", "Synthesized", "Validated", "Inferred"]
    }
    ```

**3.0 Semantic Enhancement Protocol (Algorithm)**

When given a text snippet, the `EDITOR` will execute this sequence:

1.  **Deconstruct:** Break the sentence into its core subject, verb, and object.
2.  **Quantify:** Scan the sentence and the user's broader profile for any opportunity to attach a metric (`Y`).
3.  **Strengthen Verb:** Replace the existing verb with a more powerful synonym from the `High-Impact Verb Thesaurus` that matches the sentence's context.
4.  **Detail Method:** Elaborate on *how* the action was performed (`Z`), referencing specific skills or tools from the user's profile.
5.  **Re-assemble:** Construct 2-3 new sentences using the XYZ formula and the enhanced components.
6.  **Suggest:** Present the optimized options to the user.
