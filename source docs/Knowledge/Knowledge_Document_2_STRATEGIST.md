-----

### **Knowledge Document 2/5: `STRATEGIST`**

**ID:** `KDB-STRATEGIST-2.1`
**Subject:** Computational Career Pathing & Skill Adjacency Modeling
**Description:** This document provides the `STRATEGIST` agent with the theoretical and computational models required to generate novel, viable, and data-backed career path recommendations.

**1.0 Core Framework: The Skill Adjacency Model**

The job market is modeled as a high-dimensional "skill space."

  * Each unique skill (e.g., `Python`, `Project Management`, `Stakeholder Communication`) is a dimension.
  * A **Candidate Profile** is a vector `C` in this space, with magnitudes corresponding to proficiency levels.
  * A **Job Role** is also a vector `J` in this space, representing the ideal candidate's skill profile for that role.
  * The `STRATEGIST`'s primary function is to compute the "distance" between vector `C` and various `J` vectors, and to identify `J` vectors that are "adjacent" (i.e., a short distance, requiring minimal skill acquisition).

**2.0 Technical Implementation: Skill Vectorization**

  * **Embedding Model:** Utilize a pre-trained language model fine-tuned on job descriptions and professional profiles (e.g., a custom `BERT` or `Sentence-BERT` model).
  * **Process:**
    1.  The user's skills, accomplishments, and interests from their profile are concatenated into a single document.
    2.  This document is passed through the embedding model to generate the candidate vector `C`.
    3.  The same process is applied to a database of curated job role descriptions to generate a library of job vectors `J`.

**3.0 Fit Scoring Algorithm**

The `Candidate Target Profile (CTP)` fit score is a weighted function of skill alignment and aspirational match.

`Fit_Score = (w_s * Skill_Cosine_Similarity) + (w_a * Aspiration_Alignment_Score)`

  * **`w_s` (Skill Weight):** Default `0.65`. The importance of existing skill overlap.
  * **`w_a` (Aspiration Weight):** Default `0.35`. The importance of alignment with the user's passions and career anchors.
  * **`Skill_Cosine_Similarity`:** The cosine similarity between vector `C` and vector `J`. A value between -1 and 1 (practically 0 to 1) indicating the angular proximity of the skill sets.
  * **`Aspiration_Alignment_Score`:** A calculated score (0 to 1) based on the overlap between the user's `career_anchors`/`riasec_codes` and the known attributes of the target job role `J`.

**4.0 Knowledge Base: Simulated 2025+ Role Taxonomy & Attribute Database**

This is a structured database mapping roles to their typical skill vectors and psychological attributes.

```yaml
# Sample from the Role Taxonomy Database
- role_id: "AIML_ETHICS_AUDITOR_01"
  title: "AI Bias & Ethics Auditor"
  description: "Specialist responsible for auditing AI/ML models for ethical compliance, fairness, bias, and transparency."
  required_skill_keywords: ["AI ethics", "model explainability", "fairness metrics", "LIME", "SHAP", "python", "responsible AI"]
  associated_riasec_codes: ["Investigative", "Conventional"]
  associated_career_anchors: ["Service/Dedication to a Cause", "Technical/Functional Competence"]

- role_id: "DEFI_RISK_ANALYST_03"
  title: "DeFi Protocol Risk Analyst"
  description: "Analyzes smart contracts and decentralized finance protocols for economic, technical, and security vulnerabilities."
  required_skill_keywords: ["DeFi", "smart contracts", "Solidity", "risk modeling", "blockchain analytics", "game theory"]
  associated_riasec_codes: ["Investigative", "Enterprising"]
  associated_career_anchors: ["Pure Challenge", "Technical/Functional Competence"]
```

-----

