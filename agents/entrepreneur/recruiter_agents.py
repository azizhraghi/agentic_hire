"""
Recruiter AI Agents - Multi-Agent System
==================================================
AI-powered agents for the Recruitment Espace.
Reuses BaseAgent from student multi_agent_system.

All 5 Agents:
1. JobDescriptionAgent - Generate structured job descriptions from natural language
2. LinkedInPostAgent  - Generate viral LinkedIn posts via LLM
3. CVScorerAgent      - AI-powered candidate scoring (replaces random.randint)
4. InterviewPlannerAgent - Generate interview questions + scheduling
5. RecruiterCoordinator  - Orchestrates the entire recruiter flow
"""

import os
import json
import logging
import re
import requests
from typing import Dict, List, Optional
from datetime import datetime

# --- CONFIGURATION ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


from agents.core.base_agent import BaseAgent


# =====================================================================
# 1. JOB DESCRIPTION AGENT
# =====================================================================

class JobDescriptionAgent(BaseAgent):
    """Agent 1: Generate structured job descriptions from natural language input"""
    
    def __init__(self, api_key=None, model="mistral-small-latest", use_huggingface=False, use_mistral=True):
        super().__init__(api_key, model, use_huggingface, use_mistral)
        self.name = "Job Description Generator"

    def generate_job_description(self, raw_input: str, extracted_data: dict = None) -> Dict:
        """
        Takes raw recruiter input + optional extracted data and generates a structured job spec.
        Returns a structured dict with all job details.
        """
        context = ""
        if extracted_data:
            context = f"""
Already extracted information:
- Job Title: {extracted_data.get('job_title', 'Not specified')}
- Company: {extracted_data.get('company_name', 'Not specified')}
- Location: {extracted_data.get('location', 'Not specified')}
- Skills: {', '.join(extracted_data.get('skills_required', []))}
- Experience: {extracted_data.get('experience_level', 'Not specified')}
- Contract: {extracted_data.get('contract_type', 'Not specified')}
- Salary: {extracted_data.get('salary', 'Not specified')}
- Duration: {extracted_data.get('duration', 'Not specified')}
"""

        system_prompt = """You are an expert HR consultant. Generate a complete, professional job description.
Return a JSON object with these keys:
{
    "job_title": "Professional job title",
    "company_name": "Company name or 'Non spécifié'",
    "location": "City/Country or Remote",
    "contract_type": "CDI/CDD/Freelance/Stage/Alternance",
    "experience_level": "Junior/Mid/Senior/Lead",
    "salary": "Salary range or 'Competitive'",
    "skills_required": ["skill1", "skill2", "skill3"],
    "description": "A compelling 3-4 paragraph job description in French",
    "responsibilities": ["resp1", "resp2", "resp3", "resp4"],
    "benefits": ["benefit1", "benefit2", "benefit3"],
    "requirements": ["req1", "req2", "req3"]
}
Output ONLY valid JSON. Fill in reasonable defaults for missing fields based on context."""

        prompt = f"""Generate a structured job description from this recruiter request:

"{raw_input}"
{context}
Create a professional, detailed job description. If the input is in English, still write the description in French."""

        response = self._call_llm(prompt, system_prompt)
        result = self._parse_json_response(response)
        
        # Merge with extracted data as fallback
        if extracted_data and result:
            for key in ['job_title', 'company_name', 'location', 'contract_type', 'experience_level', 'salary']:
                if not result.get(key) or result.get(key) == 'Non spécifié':
                    result[key] = extracted_data.get(key, result.get(key, 'Non spécifié'))
            if not result.get('skills_required') and extracted_data.get('skills_required'):
                result['skills_required'] = extracted_data['skills_required']
        
        return result


# =====================================================================
# 2. LINKEDIN POST AGENT (AI-Powered)
# =====================================================================

class AILinkedInPostAgent(BaseAgent):
    """Agent 2: Generate viral LinkedIn recruitment posts using LLM"""
    
    def __init__(self, api_key=None, model="mistral-small-latest", use_huggingface=False, use_mistral=True):
        super().__init__(api_key, model, use_huggingface, use_mistral)
        self.name = "LinkedIn Post Generator"

    def generate_post(self, job_data: Dict, form_url: str = "") -> str:
        """Generate a viral LinkedIn post for a job opening"""
        
        system_prompt = """You are an expert LinkedIn copywriter specialized in viral recruitment posts.
Write in FRENCH. Create an engaging, professional post that makes talent want to apply immediately.

Rules:
- Start with a strong hook emoji + catchy first line
- Use emojis strategically (not too many)
- Include the job title, company, location prominently
- List 4-6 key skills with checkmark emojis
- Add a "Why join us?" section with 3 compelling reasons
- Include salary if provided
- End with a clear call-to-action with the application link
- Add 3-5 relevant hashtags
- Keep it under 300 words
- Make it feel authentic, not generic"""

        skills = ', '.join(job_data.get('skills_required', []))
        responsibilities = '\n'.join(f"- {r}" for r in job_data.get('responsibilities', []))
        benefits = '\n'.join(f"- {b}" for b in job_data.get('benefits', []))
        
        prompt = f"""Create a viral LinkedIn recruitment post for this position:

Job Title: {job_data.get('job_title', 'N/A')}
Company: {job_data.get('company_name', 'Notre entreprise')}
Location: {job_data.get('location', 'N/A')}
Contract: {job_data.get('contract_type', 'N/A')}
Experience: {job_data.get('experience_level', 'N/A')}
Salary: {job_data.get('salary', 'Compétitif')}
Skills: {skills}
Key Responsibilities: {responsibilities}
Benefits: {benefits}
Application Link: {form_url or '[Lien dans le commentaire]'}

Job Description:
{job_data.get('description', 'N/A')}

Generate the LinkedIn post now:"""

        post_content = self._call_llm(prompt, system_prompt, max_tokens=1000)
        
        # Clean up if needed
        if post_content.startswith('"') and post_content.endswith('"'):
            post_content = post_content[1:-1]
        
        return post_content.strip()


# =====================================================================
# 3. CV SCORER AGENT
# =====================================================================

class CVScorerAgent(BaseAgent):
    """Agent 3: AI-powered candidate scoring against job requirements"""
    
    def __init__(self, api_key=None, model="mistral-small-latest", use_huggingface=False, use_mistral=True):
        super().__init__(api_key, model, use_huggingface, use_mistral)
        self.name = "CV Scorer"

    def score_candidate(self, candidate: Dict, job_data: Dict) -> Dict:
        """
        Score a single candidate against job requirements.
        Returns dict with score, reasoning, strengths, gaps.
        """
        system_prompt = """You are an expert HR recruiter evaluating candidates.
Analyze the candidate's profile against the job requirements and return a JSON object:
{
    "score": int (0-100),
    "recommendation": "Excellent Match / Good Match / Partial Match / Weak Match",
    "strengths": ["strength1", "strength2"],
    "gaps": ["gap1", "gap2"],
    "reasoning": "One sentence explaining the score",
    "interview_priority": "High / Medium / Low"
}
Be realistic and fair. Output ONLY valid JSON."""

        cv_text = candidate.get('cv_text', 'No CV provided')
        
        prompt = f"""Evaluate this candidate for the position:

POSITION:
- Title: {job_data.get('job_title', 'N/A')}
- Required Skills: {', '.join(job_data.get('skills_required', []))}
- Experience Level: {job_data.get('experience_level', 'N/A')}
- Requirements: {', '.join(job_data.get('requirements', []))}

CANDIDATE:
- Name: {candidate.get('nom', 'N/A')} {candidate.get('prenom', '')}
- CV/Profile:
{cv_text[:3000]}

Score this candidate:"""

        response = self._call_llm(prompt, system_prompt)
        result = self._parse_json_response(response)
        
        # Ensure score exists with fallback
        if not result.get('score'):
            result['score'] = 50
            result['recommendation'] = 'Unable to fully evaluate'
            result['reasoning'] = 'AI could not fully parse the candidate profile'
        
        return result

    def score_all_candidates(self, candidates: List[Dict], job_data: Dict) -> List[Dict]:
        """Score all candidates and return sorted by score"""
        scored = []
        for cand in candidates:
            ai_result = self.score_candidate(cand, job_data)
            enriched = {**cand}
            enriched['score'] = ai_result.get('score', 50)
            enriched['recommendation'] = ai_result.get('recommendation', 'N/A')
            enriched['strengths'] = ai_result.get('strengths', [])
            enriched['gaps'] = ai_result.get('gaps', [])
            enriched['reasoning'] = ai_result.get('reasoning', '')
            enriched['interview_priority'] = ai_result.get('interview_priority', 'Medium')
            scored.append(enriched)
        
        # Sort by score descending
        scored.sort(key=lambda x: x.get('score', 0), reverse=True)
        return scored


# =====================================================================
# 4. INTERVIEW PLANNER AGENT
# =====================================================================

class InterviewPlannerAgent(BaseAgent):
    """Agent 4: Generate personalized interview questions and scheduling"""
    
    def __init__(self, api_key=None, model="mistral-small-latest", use_huggingface=False, use_mistral=True):
        super().__init__(api_key, model, use_huggingface, use_mistral)
        self.name = "Interview Planner"

    def generate_interview_plan(self, candidate: Dict, job_data: Dict) -> Dict:
        """Generate personalized interview questions for a candidate"""
        
        system_prompt = """You are an expert interviewer and HR specialist.
Generate a personalized interview plan for this candidate. Return JSON:
{
    "technical_questions": ["q1", "q2", "q3"],
    "behavioral_questions": ["q1", "q2"],
    "role_specific_questions": ["q1", "q2"],
    "areas_to_probe": ["area1", "area2"],
    "recommended_duration": "30min / 45min / 60min",
    "interview_tips": "Brief tip for the interviewer"
}
Base questions on the candidate's profile gaps and the job requirements.
Write questions in FRENCH. Output ONLY valid JSON."""

        prompt = f"""Create an interview plan for:

JOB: {job_data.get('job_title', 'N/A')}
Required Skills: {', '.join(job_data.get('skills_required', []))}

CANDIDATE: {candidate.get('nom', 'N/A')} {candidate.get('prenom', '')}
Score: {candidate.get('score', 'N/A')}/100
Strengths: {', '.join(candidate.get('strengths', []))}
Gaps: {', '.join(candidate.get('gaps', []))}
CV Summary: {candidate.get('cv_text', 'N/A')[:1500]}

Generate personalized interview questions:"""

        response = self._call_llm(prompt, system_prompt)
        return self._parse_json_response(response)

    def generate_email_invitation(self, candidate: Dict, job_data: Dict, interview_date: str) -> str:
        """Generate a personalized interview invitation email"""
        
        system_prompt = """You are a professional HR communication specialist.
Write a warm, professional interview invitation email in FRENCH.
Keep it concise (max 150 words). Include the date, position, and a welcoming tone."""

        prompt = f"""Write an interview invitation email:

Candidate: {candidate.get('prenom', '')} {candidate.get('nom', '')}
Position: {job_data.get('job_title', 'N/A')}
Company: {job_data.get('company_name', 'Notre entreprise')}
Interview Date: {interview_date}
Location: {job_data.get('location', 'À définir')}

Write the email:"""

        return self._call_llm(prompt, system_prompt, max_tokens=500)


# =====================================================================
# 5. RECRUITER COORDINATOR
# =====================================================================

class RecruiterCoordinator(BaseAgent):
    """Agent 5: Orchestrates all recruiter agents"""
    
    def __init__(self, api_key=None, model="mistral-small-latest", use_huggingface=False, use_mistral=True):
        super().__init__(api_key, model, use_huggingface, use_mistral)
        self.name = "Recruiter Coordinator"
        
        # Initialize sub-agents with same config
        self.job_desc_agent = JobDescriptionAgent(api_key, model, use_huggingface, use_mistral)
        self.linkedin_agent = AILinkedInPostAgent(api_key, model, use_huggingface, use_mistral)
        self.scorer_agent = CVScorerAgent(api_key, model, use_huggingface, use_mistral)
        self.interview_agent = InterviewPlannerAgent(api_key, model, use_huggingface, use_mistral)

    def create_job_posting(self, raw_input: str, extracted_data: dict = None, form_url: str = "") -> Dict:
        """
        Full pipeline: raw input → job description → LinkedIn post
        Returns all artifacts.
        """
        logger.info("🚀 [Coordinator] Starting job posting pipeline...")
        
        # Step 1: Generate structured job description
        logger.info("📝 [Agent 1] Generating job description...")
        job_data = self.job_desc_agent.generate_job_description(raw_input, extracted_data)
        
        if not job_data:
            logger.warning("Job description generation failed, using extracted data as fallback")
            job_data = extracted_data or {}
        
        # Step 2: Generate LinkedIn post
        logger.info("📢 [Agent 2] Generating LinkedIn post...")
        linkedin_post = self.linkedin_agent.generate_post(job_data, form_url)
        
        logger.info("✅ [Coordinator] Job posting pipeline complete!")
        
        return {
            "job_data": job_data,
            "linkedin_post": linkedin_post,
        }

    def evaluate_candidates(self, candidates: List[Dict], job_data: Dict) -> List[Dict]:
        """
        Score all candidates against job requirements using AI.
        """
        logger.info(f"🧠 [Agent 3] Scoring {len(candidates)} candidates...")
        scored = self.scorer_agent.score_all_candidates(candidates, job_data)
        logger.info(f"✅ [Coordinator] Scoring complete! Top score: {scored[0].get('score', 0) if scored else 'N/A'}")
        return scored

    def plan_interviews(self, candidates: List[Dict], job_data: Dict) -> List[Dict]:
        """
        Generate interview plans for top candidates.
        """
        top_candidates = [c for c in candidates if c.get('score', 0) >= 60]
        
        logger.info(f"📋 [Agent 4] Planning interviews for {len(top_candidates)} candidates...")
        
        for cand in top_candidates:
            plan = self.interview_agent.generate_interview_plan(cand, job_data)
            cand['interview_plan'] = plan
        
        logger.info("✅ [Coordinator] Interview planning complete!")
        return top_candidates
