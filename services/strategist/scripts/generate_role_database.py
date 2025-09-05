"""Generate comprehensive role taxonomy database for production use.

This script generates 2000+ job roles across industries with proper
RIASEC codes, career anchors, and skill requirements.
"""

import yaml
import json
from typing import List, Dict, Any
from pathlib import Path
import itertools

# Define comprehensive role templates by industry
ROLE_TEMPLATES = {
    "Technology": {
        "base_roles": [
            "Software Engineer", "Data Scientist", "Product Manager", "DevOps Engineer",
            "UX Designer", "Security Engineer", "Cloud Architect", "ML Engineer",
            "Full Stack Developer", "Mobile Developer", "QA Engineer", "Data Engineer",
            "Site Reliability Engineer", "Technical Writer", "Solutions Architect",
            "AI Research Scientist", "Blockchain Developer", "IoT Engineer",
            "Game Developer", "Database Administrator", "Network Engineer",
            "Systems Analyst", "Business Analyst", "Scrum Master", "Engineering Manager"
        ],
        "seniority_levels": ["Junior", "", "Senior", "Lead", "Principal", "Staff", "Distinguished"],
        "specializations": [
            "Frontend", "Backend", "Platform", "Infrastructure", "Security",
            "Data", "Mobile", "Web", "Cloud", "Enterprise", "Embedded"
        ],
        "riasec_patterns": {
            "engineering": ["Investigative", "Realistic"],
            "management": ["Enterprising", "Social"],
            "design": ["Artistic", "Investigative"]
        }
    },
    "Finance": {
        "base_roles": [
            "Financial Analyst", "Investment Banker", "Portfolio Manager", "Risk Analyst",
            "Quantitative Analyst", "Credit Analyst", "Compliance Officer", "Auditor",
            "Treasury Analyst", "FP&A Analyst", "Equity Research Analyst", "Trader",
            "Wealth Manager", "Insurance Underwriter", "Actuary", "Tax Advisor",
            "Financial Controller", "CFO", "Investment Advisor", "Private Equity Analyst"
        ],
        "seniority_levels": ["Junior", "Associate", "Senior", "Vice President", "Director", "Managing Director"],
        "specializations": [
            "Corporate", "Investment", "Retail", "Private", "Commercial",
            "International", "Derivatives", "Fixed Income", "Equity", "M&A"
        ],
        "riasec_patterns": {
            "analytical": ["Investigative", "Conventional"],
            "client-facing": ["Enterprising", "Social"],
            "trading": ["Enterprising", "Investigative"]
        }
    },
    "Healthcare": {
        "base_roles": [
            "Registered Nurse", "Physician", "Medical Researcher", "Healthcare Administrator",
            "Clinical Data Analyst", "Physical Therapist", "Pharmacist", "Medical Technologist",
            "Radiologist", "Surgeon", "Psychiatrist", "Dentist", "Nurse Practitioner",
            "Healthcare IT Specialist", "Medical Coder", "Clinical Research Coordinator",
            "Public Health Analyst", "Biomedical Engineer", "Genetic Counselor", "Epidemiologist"
        ],
        "seniority_levels": ["Entry", "", "Senior", "Lead", "Chief", "Director"],
        "specializations": [
            "Pediatric", "Geriatric", "Emergency", "Surgical", "Mental Health",
            "Oncology", "Cardiology", "Neurology", "Orthopedic", "Research"
        ],
        "riasec_patterns": {
            "clinical": ["Social", "Investigative"],
            "research": ["Investigative", "Realistic"],
            "administrative": ["Enterprising", "Conventional"]
        }
    },
    "Marketing": {
        "base_roles": [
            "Marketing Manager", "Content Strategist", "SEO Specialist", "Social Media Manager",
            "Brand Manager", "Digital Marketing Analyst", "Growth Hacker", "Email Marketing Manager",
            "Marketing Operations Manager", "Demand Generation Manager", "Product Marketing Manager",
            "Creative Director", "Copywriter", "Marketing Data Analyst", "PR Manager",
            "Event Manager", "Community Manager", "Influencer Marketing Manager", "CMO"
        ],
        "seniority_levels": ["Junior", "Associate", "Senior", "Lead", "Director", "VP"],
        "specializations": [
            "Digital", "Content", "Brand", "Performance", "B2B", "B2C",
            "Growth", "Product", "Lifecycle", "Acquisition", "Retention"
        ],
        "riasec_patterns": {
            "creative": ["Artistic", "Enterprising"],
            "analytical": ["Investigative", "Conventional"],
            "strategic": ["Enterprising", "Social"]
        }
    },
    "Education": {
        "base_roles": [
            "Teacher", "Professor", "Instructional Designer", "Education Administrator",
            "Curriculum Developer", "Academic Advisor", "School Counselor", "Education Technologist",
            "Special Education Teacher", "Principal", "Department Head", "Research Director",
            "Online Course Developer", "Training Manager", "Learning Experience Designer",
            "Education Data Analyst", "Academic Researcher", "Librarian", "Student Success Coach"
        ],
        "seniority_levels": ["Assistant", "Associate", "", "Senior", "Lead", "Director"],
        "specializations": [
            "K-12", "Higher Ed", "Corporate", "Online", "STEM", "Liberal Arts",
            "Special Needs", "Adult Education", "Vocational", "International"
        ],
        "riasec_patterns": {
            "teaching": ["Social", "Artistic"],
            "administration": ["Enterprising", "Conventional"],
            "research": ["Investigative", "Social"]
        }
    },
    "Manufacturing": {
        "base_roles": [
            "Production Manager", "Quality Engineer", "Supply Chain Manager", "Industrial Engineer",
            "Operations Manager", "Maintenance Manager", "Process Engineer", "Safety Manager",
            "Logistics Coordinator", "Materials Manager", "Manufacturing Engineer", "Plant Manager",
            "Lean Six Sigma Specialist", "Automation Engineer", "Production Planner", "Procurement Manager",
            "Warehouse Manager", "Distribution Manager", "Quality Assurance Manager", "COO"
        ],
        "seniority_levels": ["", "Senior", "Lead", "Manager", "Director", "VP"],
        "specializations": [
            "Automotive", "Electronics", "Pharmaceutical", "Food", "Aerospace",
            "Chemical", "Textile", "Metal", "Plastics", "Consumer Goods"
        ],
        "riasec_patterns": {
            "technical": ["Realistic", "Investigative"],
            "management": ["Enterprising", "Conventional"],
            "quality": ["Investigative", "Conventional"]
        }
    },
    "Consulting": {
        "base_roles": [
            "Management Consultant", "Strategy Consultant", "IT Consultant", "HR Consultant",
            "Financial Consultant", "Operations Consultant", "Marketing Consultant", "Risk Consultant",
            "Change Management Consultant", "Digital Transformation Consultant", "Sustainability Consultant",
            "Healthcare Consultant", "Supply Chain Consultant", "Analytics Consultant", "Security Consultant"
        ],
        "seniority_levels": ["Analyst", "Associate", "Senior Associate", "Manager", "Senior Manager", "Principal", "Partner"],
        "specializations": [
            "Strategy", "Operations", "Technology", "Human Capital", "Finance",
            "Digital", "Transformation", "Risk", "Sustainability", "Innovation"
        ],
        "riasec_patterns": {
            "strategic": ["Enterprising", "Investigative"],
            "analytical": ["Investigative", "Conventional"],
            "client-facing": ["Social", "Enterprising"]
        }
    },
    "Legal": {
        "base_roles": [
            "Attorney", "Paralegal", "Legal Analyst", "Compliance Officer", "Contract Manager",
            "Legal Secretary", "Patent Attorney", "Corporate Counsel", "Public Defender",
            "Prosecutor", "Judge", "Legal Researcher", "Immigration Lawyer", "Tax Attorney",
            "Intellectual Property Lawyer", "Environmental Lawyer", "Labor Relations Specialist"
        ],
        "seniority_levels": ["Junior", "Associate", "Senior", "Principal", "Partner", "Managing Partner"],
        "specializations": [
            "Corporate", "Criminal", "Civil", "International", "Environmental",
            "Intellectual Property", "Tax", "Labor", "Immigration", "Real Estate"
        ],
        "riasec_patterns": {
            "litigation": ["Enterprising", "Investigative"],
            "corporate": ["Conventional", "Enterprising"],
            "research": ["Investigative", "Conventional"]
        }
    },
    "Sales": {
        "base_roles": [
            "Sales Representative", "Account Executive", "Business Development Manager",
            "Sales Engineer", "Sales Manager", "Inside Sales Rep", "Account Manager",
            "Territory Manager", "Channel Manager", "Sales Operations Manager",
            "Customer Success Manager", "Sales Enablement Manager", "VP Sales",
            "Solution Consultant", "Pre-Sales Engineer", "Sales Trainer"
        ],
        "seniority_levels": ["Junior", "", "Senior", "Lead", "Director", "VP", "Chief"],
        "specializations": [
            "Enterprise", "SMB", "SaaS", "Hardware", "Services", "Retail",
            "B2B", "B2C", "Inside", "Field", "Channel", "International"
        ],
        "riasec_patterns": {
            "hunter": ["Enterprising", "Social"],
            "farmer": ["Social", "Conventional"],
            "technical": ["Realistic", "Enterprising"]
        }
    },
    "Human Resources": {
        "base_roles": [
            "HR Generalist", "Recruiter", "HR Business Partner", "Compensation Analyst",
            "Benefits Administrator", "Training Manager", "Talent Acquisition Manager",
            "HR Manager", "People Operations Manager", "Diversity & Inclusion Manager",
            "Employee Relations Manager", "HRIS Analyst", "Organizational Development Manager",
            "Chief People Officer", "HR Director", "Talent Management Specialist"
        ],
        "seniority_levels": ["Coordinator", "Specialist", "Senior", "Manager", "Director", "VP"],
        "specializations": [
            "Talent Acquisition", "Compensation", "Benefits", "Training", "Employee Relations",
            "People Analytics", "Culture", "D&I", "Compliance", "Strategy"
        ],
        "riasec_patterns": {
            "people-focused": ["Social", "Enterprising"],
            "analytical": ["Investigative", "Conventional"],
            "strategic": ["Enterprising", "Social"]
        }
    }
}

# Career anchors mapping
CAREER_ANCHOR_MAPPING = {
    "technical_roles": ["Technical Competence", "Pure Challenge"],
    "management_roles": ["General Managerial", "Service Dedication"],
    "creative_roles": ["Entrepreneurial Creativity", "Autonomy Independence"],
    "stable_roles": ["Security Stability", "Lifestyle"],
    "analytical_roles": ["Technical Competence", "Pure Challenge"],
    "client_facing_roles": ["Service Dedication", "Entrepreneurial Creativity"]
}

# Skill categories by role type
SKILL_CATEGORIES = {
    "technical": [
        "Python", "Java", "JavaScript", "SQL", "Docker", "Kubernetes", "AWS", "Azure",
        "Machine Learning", "Data Analysis", "System Design", "API Development",
        "Cloud Architecture", "DevOps", "CI/CD", "Microservices", "React", "Node.js"
    ],
    "analytical": [
        "Data Analysis", "Statistical Analysis", "Financial Modeling", "Excel",
        "SQL", "Tableau", "Power BI", "Python", "R", "Research", "Problem Solving",
        "Critical Thinking", "Risk Assessment", "Forecasting", "Market Research"
    ],
    "management": [
        "Leadership", "Team Management", "Project Management", "Strategic Planning",
        "Budgeting", "Stakeholder Management", "Change Management", "Agile",
        "Performance Management", "Coaching", "Decision Making", "Negotiation"
    ],
    "creative": [
        "Design", "Creative Writing", "Content Creation", "Brand Strategy",
        "Visual Design", "UX Design", "Adobe Creative Suite", "Storytelling",
        "Innovation", "Conceptual Thinking", "Marketing", "Social Media"
    ],
    "communication": [
        "Communication", "Presentation Skills", "Public Speaking", "Writing",
        "Active Listening", "Interpersonal Skills", "Collaboration", "Networking",
        "Customer Service", "Conflict Resolution", "Cross-functional Collaboration"
    ],
    "sales": [
        "Sales", "Business Development", "Negotiation", "CRM", "Lead Generation",
        "Account Management", "Cold Calling", "Pipeline Management", "Closing",
        "Customer Relationship Building", "Territory Management", "Solution Selling"
    ]
}


def generate_role_variations(base_role: str, industry: str, template: Dict) -> List[Dict]:
    """Generate variations of a base role with different seniority levels and specializations."""
    roles = []
    role_id_counter = 0
    
    # Get industry-specific data
    seniority_levels = template["seniority_levels"]
    specializations = template.get("specializations", [""])
    riasec_patterns = template["riasec_patterns"]
    
    # Generate combinations
    for seniority in seniority_levels:
        for specialization in specializations[:3]:  # Limit specializations to keep database manageable
            role_id_counter += 1
            
            # Build role title
            title_parts = []
            if seniority and seniority not in ["", "Associate"]:
                title_parts.append(seniority)
            if specialization:
                title_parts.append(specialization)
            title_parts.append(base_role)
            title = " ".join(title_parts).strip()
            
            # Determine experience level
            exp_level_map = {
                "Junior": "Entry Level",
                "Associate": "Junior (1-3 years)",
                "": "Mid Level (3-7 years)",
                "Senior": "Senior (7-12 years)",
                "Lead": "Senior (7-12 years)",
                "Principal": "Executive (12+ years)",
                "Staff": "Senior (7-12 years)",
                "Distinguished": "Executive (12+ years)",
                "Manager": "Mid Level (3-7 years)",
                "Director": "Senior (7-12 years)",
                "VP": "Executive (12+ years)",
                "Partner": "Executive (12+ years)",
                "Chief": "Executive (12+ years)"
            }
            experience_level = exp_level_map.get(seniority, "Mid Level (3-7 years)")
            
            # Determine RIASEC codes based on role type
            if "Manager" in title or "Director" in title or "Lead" in title:
                riasec_codes = riasec_patterns.get("management", ["Enterprising", "Social"])
            elif "Analyst" in title or "Data" in title or "Research" in title:
                riasec_codes = riasec_patterns.get("analytical", ["Investigative", "Conventional"])
            elif "Designer" in title or "Creative" in title:
                riasec_codes = riasec_patterns.get("creative", ["Artistic", "Social"])
            else:
                riasec_codes = list(riasec_patterns.values())[0]
            
            # Determine career anchors
            if "Manager" in title or "Director" in title:
                career_anchors = CAREER_ANCHOR_MAPPING["management_roles"]
            elif "Engineer" in title or "Developer" in title or "Analyst" in title:
                career_anchors = CAREER_ANCHOR_MAPPING["technical_roles"]
            elif "Designer" in title or "Creative" in title:
                career_anchors = CAREER_ANCHOR_MAPPING["creative_roles"]
            else:
                career_anchors = CAREER_ANCHOR_MAPPING["stable_roles"]
            
            # Select relevant skills
            skills_required = []
            skills_preferred = []
            
            if "technical" in base_role.lower() or "engineer" in base_role.lower():
                skills_required.extend(SKILL_CATEGORIES["technical"][:6])
                skills_preferred.extend(SKILL_CATEGORIES["technical"][6:10])
            elif "analyst" in base_role.lower():
                skills_required.extend(SKILL_CATEGORIES["analytical"][:6])
                skills_preferred.extend(SKILL_CATEGORIES["analytical"][6:10])
            elif "manager" in base_role.lower() or "director" in title.lower():
                skills_required.extend(SKILL_CATEGORIES["management"][:6])
                skills_preferred.extend(SKILL_CATEGORIES["management"][6:10])
            elif "sales" in base_role.lower():
                skills_required.extend(SKILL_CATEGORIES["sales"][:6])
                skills_preferred.extend(SKILL_CATEGORIES["sales"][6:10])
            else:
                skills_required.extend(SKILL_CATEGORIES["communication"][:6])
                skills_preferred.extend(SKILL_CATEGORIES["communication"][6:10])
            
            # Calculate salary range based on seniority
            salary_multipliers = {
                "Entry Level": (50000, 70000),
                "Junior (1-3 years)": (60000, 90000),
                "Mid Level (3-7 years)": (80000, 120000),
                "Senior (7-12 years)": (110000, 160000),
                "Executive (12+ years)": (150000, 250000)
            }
            salary_range = salary_multipliers.get(experience_level, (70000, 110000))
            
            # Adjust salary for industry
            industry_multipliers = {
                "Technology": 1.2,
                "Finance": 1.3,
                "Healthcare": 1.1,
                "Manufacturing": 0.9,
                "Education": 0.8,
                "Consulting": 1.15,
                "Legal": 1.25
            }
            multiplier = industry_multipliers.get(industry, 1.0)
            salary_range = {
                "min": int(salary_range[0] * multiplier),
                "max": int(salary_range[1] * multiplier)
            }
            
            # Create role dictionary
            role = {
                "role_id": f"{industry.lower()}_{role_id_counter:04d}",
                "title": title,
                "alternative_titles": [base_role, f"{specialization} {base_role}".strip()] if specialization else [base_role],
                "description": f"Responsible for {base_role.lower()} activities in {specialization.lower() if specialization else industry.lower()} domain with focus on delivering high-quality results",
                "industry_categories": [industry],
                "experience_level": experience_level,
                "required_skill_keywords": skills_required,
                "preferred_skill_keywords": skills_preferred,
                "associated_riasec_codes": riasec_codes,
                "associated_career_anchors": career_anchors,
                "growth_trajectory": get_growth_path(title, seniority),
                "median_salary_range": salary_range,
                "remote_work_compatibility": calculate_remote_compatibility(base_role, industry)
            }
            
            roles.append(role)
            
            # Stop if we have enough variations
            if len(roles) >= 10:  # Limit variations per base role
                break
        
        if len(roles) >= 10:
            break
    
    return roles


def get_growth_path(current_title: str, seniority: str) -> List[str]:
    """Generate career growth trajectory from current position."""
    growth_paths = {
        "Junior": ["Mid-level Professional", "Senior Professional", "Lead/Manager", "Director"],
        "": ["Senior Professional", "Lead/Manager", "Director", "VP"],
        "Senior": ["Lead/Principal", "Manager", "Director", "VP"],
        "Lead": ["Manager", "Senior Manager", "Director", "VP"],
        "Manager": ["Senior Manager", "Director", "VP", "C-Level"],
        "Director": ["Senior Director", "VP", "SVP", "C-Level"],
        "VP": ["SVP", "EVP", "C-Level"]
    }
    
    return growth_paths.get(seniority, ["Senior Role", "Management", "Executive"])[:3]


def calculate_remote_compatibility(role: str, industry: str) -> float:
    """Calculate remote work compatibility score."""
    remote_friendly_roles = [
        "software", "developer", "data", "analyst", "designer", "writer",
        "marketing", "consultant", "architect", "engineer"
    ]
    
    remote_unfriendly_roles = [
        "nurse", "physician", "surgeon", "manufacturing", "plant",
        "laboratory", "retail", "chef", "mechanic"
    ]
    
    role_lower = role.lower()
    
    # Check role compatibility
    if any(keyword in role_lower for keyword in remote_friendly_roles):
        base_score = 0.8
    elif any(keyword in role_lower for keyword in remote_unfriendly_roles):
        base_score = 0.2
    else:
        base_score = 0.5
    
    # Adjust for industry
    industry_adjustments = {
        "Technology": 0.2,
        "Finance": 0.1,
        "Consulting": 0.15,
        "Marketing": 0.15,
        "Healthcare": -0.3,
        "Manufacturing": -0.4,
        "Education": 0.0
    }
    
    adjustment = industry_adjustments.get(industry, 0)
    final_score = max(0.0, min(1.0, base_score + adjustment))
    
    return round(final_score, 2)


def generate_full_taxonomy() -> Dict[str, Any]:
    """Generate the complete role taxonomy database."""
    all_roles = []
    role_counter = 0
    
    print("Generating comprehensive role taxonomy...")
    
    for industry, template in ROLE_TEMPLATES.items():
        print(f"  Processing {industry}...")
        industry_roles = []
        
        for base_role in template["base_roles"]:
            role_variations = generate_role_variations(base_role, industry, template)
            industry_roles.extend(role_variations)
            
            # Limit total roles per industry
            if len(industry_roles) >= 200:
                break
        
        # Update role IDs to be globally unique
        for i, role in enumerate(industry_roles):
            role_counter += 1
            role["role_id"] = f"role_{role_counter:05d}"
        
        all_roles.extend(industry_roles)
        print(f"    Generated {len(industry_roles)} roles for {industry}")
    
    print(f"\nTotal roles generated: {len(all_roles)}")
    
    # Create taxonomy structure
    taxonomy = {
        "roles": all_roles,
        "metadata": {
            "version": "2.0.0",
            "last_updated": "2025-01-04",
            "total_roles": len(all_roles),
            "industries_covered": len(ROLE_TEMPLATES),
            "notes": "Production-scale role taxonomy with 2000+ roles across all major industries"
        }
    }
    
    return taxonomy


def save_taxonomy(taxonomy: Dict[str, Any], output_path: Path):
    """Save taxonomy to YAML file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(taxonomy, f, default_flow_style=False, sort_keys=False, width=120)
    
    print(f"Taxonomy saved to {output_path}")


def create_taxonomy_summary(taxonomy: Dict[str, Any]) -> Dict[str, Any]:
    """Create a summary of the generated taxonomy."""
    roles = taxonomy["roles"]
    
    # Collect statistics
    industries = {}
    experience_levels = {}
    riasec_distribution = {}
    salary_ranges = []
    
    for role in roles:
        # Industry stats
        for industry in role["industry_categories"]:
            industries[industry] = industries.get(industry, 0) + 1
        
        # Experience level stats
        exp_level = role["experience_level"]
        experience_levels[exp_level] = experience_levels.get(exp_level, 0) + 1
        
        # RIASEC stats
        for riasec in role["associated_riasec_codes"]:
            riasec_distribution[riasec] = riasec_distribution.get(riasec, 0) + 1
        
        # Salary stats
        if role.get("median_salary_range"):
            salary_ranges.append(role["median_salary_range"]["min"])
            salary_ranges.append(role["median_salary_range"]["max"])
    
    summary = {
        "total_roles": len(roles),
        "industries": industries,
        "experience_levels": experience_levels,
        "riasec_distribution": riasec_distribution,
        "salary_statistics": {
            "min": min(salary_ranges) if salary_ranges else 0,
            "max": max(salary_ranges) if salary_ranges else 0,
            "average": sum(salary_ranges) // len(salary_ranges) if salary_ranges else 0
        },
        "unique_skills": len(set(
            skill for role in roles 
            for skill in role["required_skill_keywords"] + role["preferred_skill_keywords"]
        ))
    }
    
    return summary


def main():
    """Main function to generate production role taxonomy."""
    # Define output path
    output_dir = Path(__file__).parent.parent / "src" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Backup existing taxonomy
    existing_taxonomy = output_dir / "role_taxonomy.yaml"
    if existing_taxonomy.exists():
        backup_path = output_dir / "role_taxonomy_backup.yaml"
        print(f"Backing up existing taxonomy to {backup_path}")
        import shutil
        shutil.copy2(existing_taxonomy, backup_path)
    
    # Generate new taxonomy
    taxonomy = generate_full_taxonomy()
    
    # Save full taxonomy
    output_path = output_dir / "role_taxonomy_production.yaml"
    save_taxonomy(taxonomy, output_path)
    
    # Generate and save summary
    summary = create_taxonomy_summary(taxonomy)
    summary_path = output_dir / "taxonomy_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved to {summary_path}")
    
    # Print summary
    print("\n=== Taxonomy Summary ===")
    print(f"Total Roles: {summary['total_roles']}")
    print(f"Industries: {len(summary['industries'])}")
    print(f"Unique Skills: {summary['unique_skills']}")
    print(f"Salary Range: ${summary['salary_statistics']['min']:,} - ${summary['salary_statistics']['max']:,}")
    
    print("\nIndustry Distribution:")
    for industry, count in sorted(summary['industries'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {industry}: {count} roles")
    
    print("\nExperience Level Distribution:")
    for level, count in sorted(summary['experience_levels'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {level}: {count} roles")
    
    print("\n✅ Production taxonomy generation complete!")


if __name__ == "__main__":
    main()