"""
Test resume fixtures for integration testing.

This module provides sample resume data in various formats for testing
the complete workflow of the Helios Career Operations System.
"""

import json
from typing import Dict, Any, List


def get_software_engineer_resume() -> Dict[str, Any]:
    """Sample software engineer resume data."""
    return {
        "personal_info": {
            "name": "Alice Johnson",
            "email": "alice.johnson@example.com",
            "phone": "+1-555-0147",
            "location": "Seattle, WA",
            "linkedin": "linkedin.com/in/alicejohnson",
            "github": "github.com/alicejohnson"
        },
        "summary": "Senior Software Engineer with 6+ years of experience building scalable web applications and distributed systems. Expertise in Python, JavaScript, and cloud technologies.",
        "work_experience": [
            {
                "company": "Microsoft",
                "position": "Senior Software Engineer",
                "start_date": "2021-03-15",
                "end_date": "2024-01-31",
                "location": "Redmond, WA",
                "accomplishments": [
                    "Led development of microservices architecture serving 2.5M+ daily active users",
                    "Reduced API response time by 45% through database optimization and caching strategies",
                    "Mentored 8 junior developers and established code review best practices",
                    "Implemented CI/CD pipeline that reduced deployment time from 2 hours to 15 minutes",
                    "Designed and built real-time notification system handling 100K+ messages per hour"
                ],
                "technologies": ["Python", "Django", "PostgreSQL", "Redis", "Docker", "Kubernetes", "Azure", "React", "TypeScript"]
            },
            {
                "company": "Amazon",
                "position": "Software Development Engineer II",
                "start_date": "2019-07-01",
                "end_date": "2021-03-01",
                "location": "Seattle, WA",
                "accomplishments": [
                    "Built serverless data processing pipeline handling 50GB+ daily data volume",
                    "Developed REST APIs with 99.9% uptime serving 500K+ requests per day",
                    "Optimized machine learning model inference reducing latency by 60%",
                    "Led migration from monolith to microservices architecture",
                    "Collaborated with cross-functional teams of 15+ engineers and product managers"
                ],
                "technologies": ["Java", "Spring Boot", "AWS Lambda", "DynamoDB", "S3", "EC2", "Python", "TensorFlow"]
            },
            {
                "company": "Startup Innovations Inc",
                "position": "Full Stack Developer",
                "start_date": "2018-01-15",
                "end_date": "2019-06-30",
                "location": "San Francisco, CA",
                "accomplishments": [
                    "Built MVP product from scratch using React and Node.js",
                    "Implemented payment integration processing $100K+ monthly transactions",
                    "Designed responsive UI/UX for web and mobile platforms",
                    "Set up monitoring and alerting system reducing downtime by 80%",
                    "Managed database migrations and backup strategies"
                ],
                "technologies": ["JavaScript", "React", "Node.js", "Express", "MongoDB", "Stripe", "Heroku", "Git"]
            }
        ],
        "projects": [
            {
                "name": "Open Source ML Framework",
                "description": "Core contributor to scikit-learn with focus on ensemble methods",
                "start_date": "2020-01-01",
                "end_date": "ongoing",
                "technologies": ["Python", "Machine Learning", "NumPy", "Pandas", "Scikit-learn"],
                "impact": "Improved Random Forest algorithm performance by 20% for large datasets",
                "url": "github.com/scikit-learn/scikit-learn",
                "role": "Core Contributor"
            },
            {
                "name": "Personal Finance Dashboard",
                "description": "Full-stack web application for personal financial management",
                "start_date": "2019-09-01",
                "end_date": "2020-02-01",
                "technologies": ["React", "Node.js", "Express", "PostgreSQL", "D3.js", "Plaid API"],
                "impact": "Used by 500+ users for budget tracking and expense analysis",
                "url": "github.com/alicejohnson/finance-dashboard",
                "role": "Solo Developer"
            }
        ],
        "skills_inventory": {
            "programming_languages": ["Python", "JavaScript", "TypeScript", "Java", "Go", "SQL"],
            "frameworks": ["Django", "React", "Node.js", "Express", "Spring Boot", "FastAPI"],
            "databases": ["PostgreSQL", "MongoDB", "Redis", "DynamoDB", "MySQL"],
            "cloud_platforms": ["AWS", "Azure", "GCP", "Heroku"],
            "tools": ["Docker", "Kubernetes", "Git", "Jenkins", "Terraform", "Grafana"],
            "methodologies": ["Agile", "Scrum", "TDD", "CI/CD", "Microservices", "DevOps"]
        },
        "education": [
            {
                "institution": "University of Washington",
                "degree": "Bachelor of Science in Computer Science",
                "graduation_year": "2018",
                "gpa": "3.9",
                "relevant_coursework": ["Data Structures", "Algorithms", "Database Systems", "Machine Learning", "Software Engineering"]
            }
        ],
        "certifications": [
            {
                "name": "AWS Certified Solutions Architect",
                "issuer": "Amazon Web Services",
                "date": "2022-06-15",
                "credential_id": "AWS-CSA-123456"
            },
            {
                "name": "Certified Kubernetes Administrator",
                "issuer": "Cloud Native Computing Foundation",
                "date": "2023-01-20",
                "credential_id": "CKA-789012"
            }
        ]
    }


def get_data_scientist_resume() -> Dict[str, Any]:
    """Sample data scientist resume data."""
    return {
        "personal_info": {
            "name": "Dr. Robert Chen",
            "email": "robert.chen@example.com",
            "phone": "+1-555-0289",
            "location": "Austin, TX",
            "linkedin": "linkedin.com/in/robertchen",
            "github": "github.com/robertchen"
        },
        "summary": "Senior Data Scientist with PhD in Statistics and 5+ years of experience in machine learning, statistical modeling, and big data analytics.",
        "work_experience": [
            {
                "company": "Tesla",
                "position": "Senior Data Scientist",
                "start_date": "2022-01-10",
                "end_date": "present",
                "location": "Austin, TX",
                "accomplishments": [
                    "Developed predictive models for autonomous driving reducing prediction error by 35%",
                    "Built real-time anomaly detection system for manufacturing quality control",
                    "Led A/B testing framework implementation improving decision speed by 50%",
                    "Mentored team of 6 data scientists and ML engineers",
                    "Published 3 peer-reviewed papers on computer vision applications"
                ],
                "technologies": ["Python", "TensorFlow", "PyTorch", "Apache Spark", "Kubernetes", "MLflow", "Databricks"]
            },
            {
                "company": "Netflix",
                "position": "Data Scientist",
                "start_date": "2020-03-01",
                "end_date": "2021-12-31",
                "location": "Los Gatos, CA",
                "accomplishments": [
                    "Improved recommendation algorithm increasing user engagement by 15%",
                    "Built content popularity prediction model with 85% accuracy",
                    "Designed experimentation platform for content optimization",
                    "Analyzed viewing patterns across 200M+ global subscribers",
                    "Collaborated with product teams to drive data-informed decisions"
                ],
                "technologies": ["Python", "Scala", "Apache Spark", "Kafka", "Elasticsearch", "Jupyter", "R"]
            }
        ],
        "projects": [
            {
                "name": "COVID-19 Spread Prediction Model",
                "description": "Epidemiological model for predicting COVID-19 transmission patterns",
                "start_date": "2020-03-01",
                "end_date": "2020-12-01",
                "technologies": ["Python", "PyMC3", "Bayesian Statistics", "Matplotlib", "Plotly"],
                "impact": "Model used by local health departments for policy decisions",
                "url": "github.com/robertchen/covid-prediction",
                "role": "Lead Researcher"
            }
        ],
        "skills_inventory": {
            "programming_languages": ["Python", "R", "SQL", "Scala", "MATLAB"],
            "ml_frameworks": ["TensorFlow", "PyTorch", "Scikit-learn", "XGBoost", "Keras"],
            "big_data": ["Apache Spark", "Hadoop", "Kafka", "Databricks", "Snowflake"],
            "visualization": ["Matplotlib", "Plotly", "Tableau", "D3.js", "Seaborn"],
            "cloud_platforms": ["AWS", "GCP", "Azure"],
            "statistics": ["Bayesian Statistics", "Time Series Analysis", "A/B Testing", "Causal Inference"]
        },
        "education": [
            {
                "institution": "Stanford University",
                "degree": "PhD in Statistics",
                "graduation_year": "2019",
                "dissertation": "Bayesian Methods for High-Dimensional Time Series Analysis"
            },
            {
                "institution": "UC Berkeley",
                "degree": "Master of Science in Mathematics",
                "graduation_year": "2015",
                "gpa": "3.95"
            }
        ],
        "publications": [
            {
                "title": "Deep Learning for Autonomous Vehicle Perception",
                "journal": "IEEE Transactions on Intelligent Transportation Systems",
                "year": "2023",
                "authors": ["R. Chen", "A. Smith", "M. Johnson"]
            }
        ]
    }


def get_product_manager_resume() -> Dict[str, Any]:
    """Sample product manager resume data."""
    return {
        "personal_info": {
            "name": "Sarah Williams",
            "email": "sarah.williams@example.com",
            "phone": "+1-555-0356",
            "location": "New York, NY",
            "linkedin": "linkedin.com/in/sarahwilliams"
        },
        "summary": "Senior Product Manager with 7+ years of experience driving product strategy and execution for B2B SaaS platforms. Proven track record of launching successful products that generate $10M+ in annual revenue.",
        "work_experience": [
            {
                "company": "Salesforce",
                "position": "Senior Product Manager",
                "start_date": "2021-06-01",
                "end_date": "present",
                "location": "San Francisco, CA",
                "accomplishments": [
                    "Led product roadmap for CRM analytics platform serving 50K+ enterprise customers",
                    "Launched AI-powered lead scoring feature increasing conversion rates by 28%",
                    "Managed cross-functional team of 25+ engineers, designers, and data scientists",
                    "Drove $15M annual revenue growth through new product initiatives",
                    "Established customer feedback loops and data-driven decision making processes"
                ],
                "technologies": ["Salesforce Platform", "Tableau", "Jira", "Confluence", "SQL", "Python"]
            },
            {
                "company": "HubSpot",
                "position": "Product Manager",
                "start_date": "2019-02-01",
                "end_date": "2021-05-31",
                "location": "Cambridge, MA",
                "accomplishments": [
                    "Launched marketing automation suite adopted by 10K+ customers in first year",
                    "Reduced customer churn by 22% through improved onboarding experience",
                    "Conducted 100+ customer interviews to validate product-market fit",
                    "Coordinated go-to-market strategy with sales and marketing teams",
                    "Achieved 95% customer satisfaction score for new product features"
                ],
                "technologies": ["HubSpot CRM", "Mixpanel", "Google Analytics", "A/B Testing Tools"]
            }
        ],
        "projects": [
            {
                "name": "Mobile App Product Strategy",
                "description": "Led end-to-end mobile app development from concept to 100K+ downloads",
                "start_date": "2020-01-01",
                "end_date": "2020-12-01",
                "technologies": ["Product Strategy", "User Research", "Agile", "Mobile Analytics"],
                "impact": "Generated $2M in additional annual revenue",
                "role": "Product Lead"
            }
        ],
        "skills_inventory": {
            "product_management": ["Product Strategy", "Roadmap Planning", "User Research", "Market Analysis"],
            "analytics": ["SQL", "Tableau", "Google Analytics", "Mixpanel", "A/B Testing"],
            "methodologies": ["Agile", "Scrum", "Design Thinking", "Lean Startup", "OKRs"],
            "tools": ["Jira", "Confluence", "Figma", "Miro", "Slack", "Notion"],
            "business_skills": ["Strategic Planning", "Stakeholder Management", "P&L Management", "Go-to-Market"]
        },
        "education": [
            {
                "institution": "Harvard Business School",
                "degree": "Master of Business Administration",
                "graduation_year": "2018",
                "specialization": "Technology and Operations Management"
            },
            {
                "institution": "MIT",
                "degree": "Bachelor of Science in Computer Science",
                "graduation_year": "2016",
                "gpa": "3.8"
            }
        ]
    }


def get_resume_variations() -> List[Dict[str, Any]]:
    """Get multiple resume variations for testing."""
    return [
        get_software_engineer_resume(),
        get_data_scientist_resume(),
        get_product_manager_resume()
    ]


def get_invalid_resume_data() -> List[Dict[str, Any]]:
    """Get invalid resume data for error testing."""
    return [
        # Missing required fields
        {
            "personal_info": {"name": "Invalid User"}
            # Missing work_experience, skills, etc.
        },
        # Invalid data types
        {
            "personal_info": "not a dictionary",
            "work_experience": "not a list",
            "skills_inventory": 123
        },
        # Empty data
        {},
        # Malformed dates
        {
            "personal_info": {"name": "Date Error User", "email": "test@example.com"},
            "work_experience": [{
                "company": "Test Corp",
                "position": "Developer",
                "start_date": "invalid-date",
                "end_date": "2024-13-45"  # Invalid month/day
            }]
        }
    ]