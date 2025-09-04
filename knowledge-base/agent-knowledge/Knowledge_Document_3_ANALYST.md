-----

### **Knowledge Document 3/5: `ANALYST (Helios Core Engine)`**

**ID:** `KDB-ANALYST-3.0`
**Subject:** Multi-Source Data Fusion & Resume-to-Market Analysis Pipeline
**Description:** This document contains the core technical specifications, data schemas, and analytical models for the `ANALYST` agent's 6-step pipeline. This is the heart of the Helios system.

**1.0 Step 1: Resume Deconstruction (NLP)**

  * **Primary Models:**
      * NER (Named Entity Recognition): `spaCy` with a custom-trained model for professional contexts.
      * Semantic Analysis: `Sentence-BERT` for understanding the meaning and impact of accomplishment statements.
  * **NER Extraction Schema:**
      * `SKILL`: Technical and soft skills (e.g., `Python`, `Kubernetes`, `Stakeholder Management`).
      * `TOOL`: Specific software/platforms (e.g., `JIRA`, `Tableau`, `Salesforce`).
      * `METRIC`: Quantifiable outcomes (e.g., `15%`, `$2.5M`, `3 weeks`).
      * `ACTION_VERB`: The verb leading a bullet point (e.g., `Architected`, `Managed`, `Accelerated`).
      * `RESPONSIBILITY`: The core duty described.

**2.0 Step 2: Market Correlation (Simulated DB Query)**
The agent will query simulated, structured databases with the following schemas:

  * **`Market_Jobs_DB` (Simulated LinkedIn/Otta):**
    ```json
    {
      "job_id": "string",
      "role_title": "string",
      "company_name": "string",
      "location": "string", // Incl. "Remote"
      "post_date": "date",
      "required_skills": ["array", "of", "strings"],
      "full_description_text": "string"
    }
    ```
  * **`Compensation_DB` (Simulated Levels.fyi/Glassdoor):**
    ```json
    {
      "role_title": "string",
      "company_name": "string",
      "level": "string", // e.g., L4, Senior, IC2
      "location": "string",
      "year": 2025,
      "base_salary_usd": "integer",
      "stock_grant_usd": "integer",
      "bonus_usd": "integer"
    }
    ```

**3.0 Step 3: Resume Optimization (ATS Simulation)**

  * **ATS Simulation Model:** A weighted scoring system based on leading ATS platforms (Greenhouse, Lever, iCIMS).
  * **Scoring Criteria:**
      * `Keyword Match Score (40%)`: Cosine similarity between resume text and job description keywords.
      * `Format Parsability Score (30%)`: Penalties for tables, columns, images, and non-standard fonts. Score is based on the success rate of the NER extraction in Step 1.
      * `Quantification Score (20%)`: Percentage of experience bullet points containing a `METRIC` entity.
      * `Action Verb Score (10%)`: Percentage of bullet points starting with a high-impact action verb (see verb list below).
  * **High-Impact Action Verb List (Sample):**
      * **Technical:** Architected, Engineered, Deployed, Refactored, Automated.
      * **Management:** Orchestrated, Governed, Mentored, Scaled, Piloted.
      * **Growth/Sales:** Accelerated, Evangelized, Penetrated, Negotiated, Captured.
      * **Analysis:** Synthesized, Modeled, Forecasted, Quantified, Inferred.

**4.0 Step 4: Skill Recalibration**

  * **The Skill Framing Matrix:** A 2x2 matrix used to classify every skill identified on the user's resume relative to the target role.
      * **Quadrant I (Leverage):** High Candidate Proficiency & High Market Demand. *Action: Feature prominently in the summary and headlines.*
      * **Quadrant II (Upskill):** Low Candidate Proficiency & High Market Demand. *Action: Identify as a "Critical Gap" and recommend courses.*
      * **Quadrant III (Maintain):** High Candidate Proficiency & Low Market Demand. *Action: List in the skills section but de-emphasize in bullet points. These are "Deprioritized Experiences."*
      * **Quadrant IV (De-emphasize):** Low Candidate Proficiency & Low Market Demand. *Action: Remove from the resume to save space.*

**5.0 Steps 5 & 6:** The `Career Path Inference Engine` uses the output of the Skill Framing Matrix to define Horizons 1-3. The `Final Report Generation` synthesizes all findings into the master JSON output.

-----

