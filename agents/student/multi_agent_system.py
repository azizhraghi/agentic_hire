"""
AI Job Scout - Multi-Agent System
==================================================
Complete autonomous agents with WORKING SCRAPERS + Demo Mode
Refactored for AgenticHire

All 7 Agents:
1. CVAnalyzerAgent - Deep CV understanding
2. JobAnalyzerAgent - Extract requirements & structure
3. MatcherAgent - Semantic matching & scoring
4. CVOptimizerAgent - Tailor CV for specific job
5. WriterAgent - Cover letters & messages
6. AIScraperAgent - Smart multi-source scraping
7. CoordinatorAgent - Orchestrates the entire flow
"""

import os
import time
import json
import logging
import requests
import re
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

# --- CONFIGURATION ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import fix matcher
try:
    from .matcher_fix import patch_matcher_agent, patch_job_analyzer
    MATCHER_FIX_AVAILABLE = True
except ImportError:
    MATCHER_FIX_AVAILABLE = False

# Import tools
try:
    from .tools.job_scraper import ImprovedJobScraper
except ImportError:
    # Fallback or local import if running standalone
    try:
        from job_scraper import ImprovedJobScraper
    except ImportError:
        class ImprovedJobScraper:
            def scrape_all_sources(self, *args, **kwargs): return []

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- AGENT BASE CLASS ---

class BaseAgent:
    """Base class for all AI agents - SUPPORTS GEMINI, HUGGINGFACE, OR MISTRAL"""
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: str = "mistral-small-latest", 
        use_huggingface: bool = False,
        use_mistral: bool = True
    ):
        self.api_key = api_key or os.getenv('MISTRAL_API_KEY') or os.getenv('HUGGINGFACE_TOKEN') or os.getenv('GOOGLE_API_KEY')
        self.model = model
        self.use_huggingface = use_huggingface
        self.use_mistral = use_mistral
        self.name = "Base Agent"
        
        # HuggingFace API URL
        self.hf_api_url = f"https://api-inference.huggingface.co/models/{model}"
        
        # Mistral API URL
        self.mistral_api_url = "https://api.mistral.ai/v1/chat/completions"

    def _call_llm(self, prompt: str, system_prompt: str = None, max_tokens: int = 4000) -> str:
        """Call LLM (routes to correct provider)"""
        try:
            if self.use_mistral:
                return self._call_mistral(prompt, system_prompt, max_tokens)
            elif self.use_huggingface:
                return self._call_huggingface(prompt, system_prompt, max_tokens)
            else:
                return self._call_gemini(prompt, system_prompt, max_tokens)
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return "{}"

    def _call_mistral(self, prompt: str, system_prompt: str = None, max_tokens: int = 4000) -> str:
        """Call Mistral AI API"""
        if not self.api_key:
            logger.warning("No Mistral API key provided")
            return "{}"
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(self.mistral_api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Mistral API error: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    def _call_huggingface(self, prompt: str, system_prompt: str = None, max_tokens: int = 4000) -> str:
        """Call HuggingFace Inference API - FAST & FREE!"""
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        
        # Format prompt for instruction-tuned models
        full_prompt = f"<s>[INST] "
        if system_prompt:
            full_prompt += f"<<SYS>>\n{system_prompt}\n<</SYS>>\n\n"
        full_prompt += f"{prompt} [/INST]"
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.5,
                "return_full_text": False
            }
        }
        
        try:
            response = requests.post(self.hf_api_url, headers=headers, json=payload, timeout=30)
            result = response.json()
            
            if isinstance(result, list) and 'generated_text' in result[0]:
                return result[0]['generated_text']
            elif isinstance(result, dict) and 'error' in result:
                logger.error(f"HuggingFace Error: {result['error']}")
                return "{}"
            return str(result)
            
        except Exception as e:
            logger.error(f"HuggingFace API failed: {e}")
            return "{}"

    def _call_gemini(self, prompt: str, system_prompt: str = None, max_tokens: int = 4000) -> str:
        """Call Gemini API with retry logic (ORIGINAL CODE)"""
        # Note: Keeps original logic but adapted for this class structure
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\nUSER PROMPT:\n{prompt}"
            
        data = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": max_tokens}
        }
        
        try:
            response = requests.post(url, json=data, headers={'Content-Type': 'application/json'}, timeout=30)
            if response.status_code != 200:
                logger.error(f"Gemini API Error: {response.text}")
                return "{}"
                
            result = response.json()
            if 'candidates' in result and result['candidates']:
                return result['candidates'][0]['content']['parts'][0]['text']
            return "{}"
        except Exception as e:
            logger.error(f"Gemini call failed: {e}")
            return "{}"

    def _parse_json_response(self, text: str) -> Dict:
        """Extract JSON from LLM response - robust for gemini-2.5-flash"""
        if not text:
            return {}
            
        # Clean markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        
        # Try to find JSON object
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1:
            json_str = text[start:end+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
                
        # Fallback: simple extraction if structure is known
        try:
            return json.loads(text)
        except:
            logger.warning(f"Failed to parse JSON from {self.name}")
            return {}

# --- 1. CV ANALYZER AGENT ---

class CVAnalyzerAgent(BaseAgent):
    """Agent 1: Analyze CV content"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "mistral-small-latest", use_huggingface: bool = False, use_mistral: bool = True):
        super().__init__(api_key, model, use_huggingface, use_mistral)
        self.name = "CV Analyzer"

    def analyze_cv(self, cv_text: str) -> Dict:
        """Analyze CV and extract insights"""
        system_prompt = """You are a senior HR Tech Analyst with 15+ years of experience screening candidates across tech, finance, and consulting.

Your task: Deeply analyze this CV/resume to extract structured insights. The CV may be in French or English — handle both.

Analysis criteria:
- **Profile Type**: Classify as "Junior" (<2yr exp or student/intern), "Mid" (2-5yr), "Senior" (5-10yr), or "Exec" (10yr+ or C-level/VP)
- **Primary Role**: The single most accurate job title for this person right now (e.g., "Machine Learning Engineer", not just "Engineer")
- **Technical Skills**: Extract ALL technical skills mentioned (languages, frameworks, tools, platforms). Be exhaustive — include skills inferred from project descriptions
- **Soft Skills**: Leadership, communication, teamwork, etc. Only include if clearly evidenced
- **Experience Years**: Total professional experience (internships count as 0.5yr each). Return integer
- **Strengths**: 3-5 unique differentiators that make this candidate stand out
- **Recommended Roles**: 3-5 job titles this person could realistically apply to, ordered by relevance
- **Education Level**: Highest degree completed

Return ONLY a valid JSON object:
{
    "profile_type": "Junior|Mid|Senior|Exec",
    "primary_role": "string",
    "technical_skills": ["skill1", "skill2", ...],
    "soft_skills": ["skill1", "skill2"],
    "experience_years": integer,
    "strengths": ["strength1", "strength2", "strength3"],
    "recommended_roles": ["role1", "role2", "role3"],
    "education_level": "Bac|BSc|MSc|PhD|MBA|None"
}

IMPORTANT: Output raw JSON only. No markdown, no explanation, no preamble."""
        
        response = self._call_llm(f"Analyze this CV thoroughly:\n\n{cv_text[:4000]}", system_prompt)
        return self._parse_json_response(response)

# --- 2. JOB ANALYZER AGENT ---

class JobAnalyzerAgent(BaseAgent):
    """Agent 2: Analyze job postings"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "mistral-small-latest", use_huggingface: bool = False, use_mistral: bool = True):
        super().__init__(api_key, model, use_huggingface, use_mistral)
        self.name = "Job Analyzer"
        
        # Apply fix if available
        if MATCHER_FIX_AVAILABLE:
            patch_job_analyzer(self)

    def analyze_job(self, job_title: str, job_description: str, company: str = "Unknown") -> Dict:
        """Analyze job posting"""
        # This method might be monkey-patched by MATCHER_FIX
        system_prompt = """You are a Technical Recruiter with deep expertise in parsing job postings. You can identify true requirements vs. "wish list" items.

Your task: Analyze this job posting and extract structured requirements.

Guidelines:
- **Required vs Preferred**: Only mark skills as "required" if the posting uses words like "must have", "required", "essential". Everything else is "preferred"
- **Experience Level**: Infer from context. "0-2yr" = Entry/Junior, "2-5yr" = Mid, "5+yr" = Senior, "Lead/Principal" = Senior+
- **Role Focus**: Be specific (e.g., "Backend/ML" not just "Backend")
- **Red Flags**: Identify concerning patterns (unrealistic requirements, too many hats, vague description, no salary info for senior roles)
- If the description is very short or vague, still extract what you can and note it in red_flags

Return ONLY valid JSON:
{
    "required_skills": ["skill1", "skill2"],
    "preferred_skills": ["skill1", "skill2"],
    "experience_level": "Entry|Junior|Mid|Senior|Lead",
    "role_focus": "string",
    "key_responsibilities": ["responsibility1", "responsibility2"],
    "red_flags": ["flag1"] or [],
    "salary_range": "string or Unknown"
}

Output raw JSON only."""
        
        prompt = f"Job: {job_title} at {company}\n\nDescription:\n{job_description[:3000]}"
        response = self._call_llm(prompt, system_prompt)
        return self._parse_json_response(response)

# --- 3. MATCHER AGENT ---

class MatcherAgent(BaseAgent):
    """Agent 3: Match CV to jobs"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "mistral-small-latest", use_huggingface: bool = False, use_mistral: bool = True):
        super().__init__(api_key, model, use_huggingface, use_mistral)
        self.name = "Matcher"
        
        # Apply fix if available
        if MATCHER_FIX_AVAILABLE:
            patch_matcher_agent(self)

    def calculate_match(self, cv_analysis: Dict, job_analysis: Dict, job_title: str) -> Dict:
        """Calculate match score"""
        # This method might be monkey-patched by MATCHER_FIX
        system_prompt = """You are a Talent Matching Engine. Your job is to produce accurate, consistent match scores between a candidate and a job.

SCORING RUBRIC — Use this exact weighted formula:

1. **Technical Skills Match (40%)**: What % of REQUIRED skills does the candidate have?
   - 100% match = 40 points
   - 75% match = 30 points
   - 50% match = 20 points
   - <25% match = 5 points
   - Bonus: +5 if candidate has preferred skills too

2. **Experience Level Fit (25%)**: Does candidate's seniority match the job?
   - Exact match = 25 points
   - One level below (e.g., Junior applying to Mid) = 15 points
   - One level above = 20 points
   - Two+ levels off = 5 points

3. **Role Alignment (20%)**: Is the candidate's primary role relevant to this job?
   - Direct match (e.g., "ML Engineer" → "Machine Learning Engineer") = 20 points
   - Adjacent role (e.g., "Data Scientist" → "ML Engineer") = 12 points
   - Tangential (e.g., "Frontend Dev" → "ML Engineer") = 4 points

4. **Education & Extras (15%)**: Education level, certifications, domain knowledge
   - Strong fit = 15 points
   - Adequate = 10 points
   - Weak = 5 points

RECOMMENDATION THRESHOLDS:
- 80-100: "Strong Match" → priority: "Must Apply"
- 60-79: "Good Match" → priority: "Consider"
- 40-59: "Potential" → priority: "Consider"
- 0-39: "Weak Match" → priority: "Pass"

Return ONLY valid JSON:
{
    "overall_match_score": integer (0-100),
    "matching_skills": ["skill1", "skill2"],
    "missing_skills": ["skill1", "skill2"],
    "recommendation": "Strong Match|Good Match|Potential|Weak Match",
    "application_tips": ["actionable tip 1", "actionable tip 2"],
    "priority": "Must Apply|Consider|Pass"
}

Be STRICT and CONSISTENT. A frontend developer with no ML skills should NOT score above 30 for an ML Engineer role."""
        
        prompt = f"""CANDIDATE PROFILE:
- Primary Role: {cv_analysis.get('primary_role', 'Unknown')}
- Experience: {cv_analysis.get('experience_years', 0)} years ({cv_analysis.get('profile_type', 'Unknown')} level)
- Technical Skills: {', '.join(cv_analysis.get('technical_skills', []))}
- Soft Skills: {', '.join(cv_analysis.get('soft_skills', []))}
- Education: {cv_analysis.get('education_level', 'Unknown')}
- Strengths: {', '.join(cv_analysis.get('strengths', []))}

JOB REQUIREMENTS ({job_title}):
- Required Skills: {', '.join(job_analysis.get('required_skills', []))}
- Preferred Skills: {', '.join(job_analysis.get('preferred_skills', []))}
- Experience Level: {job_analysis.get('experience_level', 'Unknown')}
- Role Focus: {job_analysis.get('role_focus', 'Unknown')}
- Key Responsibilities: {', '.join(job_analysis.get('key_responsibilities', []))}

Score this match using the rubric."""
        
        response = self._call_llm(prompt, system_prompt)
        return self._parse_json_response(response)

# --- 4. CV OPTIMIZER AGENT ---

class CVOptimizerAgent(BaseAgent):
    """Agent 4: Optimize CV for jobs"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "mistral-small-latest", use_huggingface: bool = False, use_mistral: bool = True):
        super().__init__(api_key, model, use_huggingface, use_mistral)
        self.name = "CV Optimizer"

    def optimize_cv(self, cv_text: str, job_title: str, job_description: str) -> str:
        """Tailor CV for specific job"""
        system_prompt = """You are a Professional Resume Writer specializing in ATS-optimized resumes for the tech industry.

Your task: Rewrite the candidate's CV to maximize their chances for the target job.

RULES:
1. **Never fabricate** experience, skills, or qualifications. Only rephrase and emphasize what exists
2. **ATS Keywords**: Mirror exact keywords from the job description (e.g., if the job says "CI/CD", use "CI/CD" not "continuous integration")
3. **Quantify impact**: Turn vague statements into measurable results (e.g., "Improved performance" → "Improved API response time by 40%")
4. **Relevance ordering**: Put the most job-relevant skills and experience first
5. **Language**: Write in the same language as the original CV (if French, stay in French)

OUTPUT FORMAT (Markdown):

## Professional Summary
[3-4 sentences positioning the candidate for this specific role]

## Key Skills
[Bullet list of 8-12 skills, prioritized by relevance to the job]

## Relevant Experience
[2-3 most relevant experiences with quantified achievements]

## Education
[Degrees and certifications]"""
        
        prompt = f"""TARGET JOB: {job_title}

JOB DESCRIPTION:
{job_description[:1500]}

ORIGINAL CV:
{cv_text[:3000]}

Rewrite and optimize this CV for the target job."""
        
        return self._call_llm(prompt, system_prompt)

# --- 5. WRITER AGENT ---

class WriterAgent(BaseAgent):
    """Agent 5: Write application materials"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "mistral-small-latest", use_huggingface: bool = False, use_mistral: bool = True):
        super().__init__(api_key, model, use_huggingface, use_mistral)
        self.name = "Writer"

    def write_cover_letter(self, cv_analysis: Dict, job_title: str, company: str, job_description: str) -> str:
        """Generate cover letter"""
        system_prompt = f"""You are a Career Coach who writes compelling, personalized cover letters that get interviews.

GUIDELINES:
1. **Opening hook**: Start with something specific about {company} — their product, mission, recent news, or values. NO generic "I am writing to apply for…"
2. **Value proposition**: In 2-3 paragraphs, connect the candidate's TOP relevant experiences directly to what the job needs. Use the STAR method (Situation → Task → Action → Result)
3. **Authenticity**: Write in first person, conversational but professional tone. Avoid buzzwords like "synergy", "leverage", "passionate"
4. **Closing**: Express genuine interest and suggest a next step
5. **Length**: 250-350 words maximum
6. **Language**: Match the language of the job description (French job → French letter). If unsure, write in English

Do NOT use placeholder brackets like [Company Name]. Use the actual values provided."""
        
        prompt = f"""Write a cover letter for this application:

ROLE: {job_title} at {company}

CANDIDATE:
- Current Role: {cv_analysis.get('primary_role', 'Professional')}
- Key Skills: {', '.join(cv_analysis.get('technical_skills', [])[:8])}
- Experience: {cv_analysis.get('experience_years', 0)} years
- Strengths: {', '.join(cv_analysis.get('strengths', []))}
- Education: {cv_analysis.get('education_level', 'Unknown')}

JOB DESCRIPTION:
{job_description[:1500]}

Write the cover letter now."""
        
        return self._call_llm(prompt, system_prompt)

    def write_linkedin_message(self, cv_analysis: Dict, job_title: str, company: str) -> str:
        """Generate LinkedIn connection request"""
        system_prompt = """You are a networking expert. Write a LinkedIn connection request message.

RULES:
- Maximum 280 characters (LinkedIn limit)
- Be specific: mention the exact role and one relevant skill/experience
- Sound human, not robotic. No "Dear Sir/Madam"
- Include a soft call to action ("Would love to chat about…")
- Output ONLY the message text, nothing else"""
        
        prompt = f"""Write a LinkedIn message to a recruiter at {company} about the {job_title} role.
I am a {cv_analysis.get('primary_role', 'professional')} with {cv_analysis.get('experience_years', 0)} years of experience.
My top skills: {', '.join(cv_analysis.get('technical_skills', [])[:3])}."""
        return self._call_llm(prompt, system_prompt)

# --- 6. SCRAPER AGENT (Using Tools) ---

class AIScraperAgent(BaseAgent):
    """Agent 6: Web scraping with CV-aware keyword search"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "mistral-small-latest", use_huggingface: bool = False, use_mistral: bool = True):
        super().__init__(api_key, model, use_huggingface, use_mistral)
        self.name = "Scraper"
        self.tool = ImprovedJobScraper()

    def generate_profile_demo_jobs(self, cv_analysis: Dict) -> List[Dict]:
        """Use AI to generate realistic demo jobs matching the user's actual profile"""
        skills = ", ".join(cv_analysis.get("technical_skills", [])[:5])
        role = cv_analysis.get("primary_role", "Developer")
        
        system_prompt = f"""Generate 5 realistic job postings for a {role} with skills: {skills}.
        Return a JSON list of objects with keys: title, company, location, description, url, source.
        Make them sound authentic."""
        
        response = self._call_llm(f"Generate 5 jobs for {role}", system_prompt)
        jobs = self._parse_json_response(response)
        
        if isinstance(jobs, list):
            # Enforce structure
            for j in jobs:
                j['source'] = 'Demo (AI)'
                j['url'] = '#'
            return jobs
        return self.get_generic_demo_jobs()

    def get_generic_demo_jobs(self) -> List[Dict]:
        """Fallback generic demo jobs"""
        return [
            {
                "title": "Senior Python Developer",
                "company": "TechCorp AI",
                "location": "Remote",
                "description": "We are looking for an expert in Python, Django, and AI agents. Nice to have: React experience.",
                "url": "#",
                "source": "Demo"
            },
            {
                "title": "Full Stack Engineer",
                "company": "StartupX",
                "location": "Paris, France",
                "description": "Join our fast-paced team building the future of recruitment. Stack: Next.js, FastAPI, PostgreSQL.",
                "url": "#",
                "source": "Demo"
            }
        ]

# --- 7. COORDINATOR AGENT ---

class CoordinatorAgent(BaseAgent):
    """Agent 7: Coordinate all other agents"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "mistral-small-latest", use_huggingface: bool = False, use_mistral: bool = True):
        super().__init__(api_key, model, use_huggingface, use_mistral)
        self.name = "Coordinator"
        
        # Initialize sub-agents
        self.cv_agent = CVAnalyzerAgent(api_key, model, use_huggingface, use_mistral)
        self.job_agent = JobAnalyzerAgent(api_key, model, use_huggingface, use_mistral)
        self.matcher = MatcherAgent(api_key, model, use_huggingface, use_mistral)
        self.optimizer = CVOptimizerAgent(api_key, model, use_huggingface, use_mistral)
        self.writer = WriterAgent(api_key, model, use_huggingface, use_mistral)
        self.scraper = AIScraperAgent(api_key, model, use_huggingface, use_mistral)

    def run_full_pipeline(self, cv_text: str, job_data: Dict) -> Dict:
        """Run complete pipeline for one job"""
        # 1. Analyze Job
        job_analysis = self.job_agent.analyze_job(
            job_data['title'],
            job_data['description'],
            job_data['company']
        )
        
        # 2. Optimize CV
        optimized_cv = self.optimizer.optimize_cv(
            cv_text,
            job_data['title'],
            job_data['description']
        )
        
        # 3. Analyze CV (Original) - Assuming we have it, but for purity re-analyze
        cv_analysis = self.cv_agent.analyze_cv(cv_text)
        
        # 4. Write Cover Letter
        cl = self.writer.write_cover_letter(
            cv_analysis,
            job_data['title'],
            job_data['company'],
            job_data['description']
        )
        
        # 5. Write LinkedIn Message
        li_msg = self.writer.write_linkedin_message(
            cv_analysis,
            job_data['title'],
            job_data['company']
        )
        
        return {
            "job_analysis": job_analysis,
            "optimized_cv": optimized_cv,
            "cover_letter": cl,
            "linkedin_message": li_msg
        }

    def intelligent_job_search(self, cv_text: str, jobs_per_site: int = 5, use_demo: bool = False, 
                             user_location: str = "", selected_sources: List[str] = None, 
                             include_remote: bool = True, progress_callback=None, 
                             cached_cv_analysis: Dict = None) -> List[Dict]:
        """Search multiple sites using CV-derived keywords and analyze jobs"""
        
        def update_progress(text, pct):
            if progress_callback:
                progress_callback(text, pct)
        
        logger.info("🚀 Starting Intelligent Job Search...")
        update_progress("🧠 Agent 1: Analyzing CV...", 10)
        
        # 1. Analyze CV
        if cached_cv_analysis:
            cv_analysis = cached_cv_analysis
        else:
            cv_analysis = self.cv_agent.analyze_cv(cv_text)
        
        # 2. Extract Keywords
        keywords = cv_analysis.get('technical_skills', [])[:3]
        role = cv_analysis.get('primary_role')
        if role:
            keywords.insert(0, role)
        
        update_progress(f"🔍 Agent 6: Scraping jobs for {keywords}...", 30)
        
        # 3. Scrape Jobs
        if use_demo:
             update_progress("🎬 Demo Mode: Generating realistic jobs...", 40)
             raw_jobs = self.scraper.generate_profile_demo_jobs(cv_analysis)
        else:
             raw_jobs = self.scraper.tool.scrape_all_sources(keywords, max_jobs=jobs_per_site, location=user_location)

        if not raw_jobs:
            logger.warning("No jobs found")
            return []
            
        update_progress(f"✨ Found {len(raw_jobs)} jobs. Agents 2 & 3: Analyzing & Matching...", 50)
        
        # 4. Match & Analyze each job
        analyzed_jobs = []
        total = len(raw_jobs)
        
        for i, job in enumerate(raw_jobs):
            # Analyze
            job_analysis = self.job_agent.analyze_job(
                job.get('title', ''), 
                job.get('description', ''),
                job.get('company', '')
            )
            
            # Match
            match_result = self.matcher.calculate_match(
                cv_analysis,
                job_analysis,
                job.get('title', '')
            )
            
            # Enrich job object
            job['ai_analysis'] = {
                'job_details': job_analysis,
                'match_result': match_result
            }
            job['ai_match_score'] = match_result.get('overall_match_score', 0)
            job['ai_priority'] = match_result.get('priority', 'Unknown')
            
            analyzed_jobs.append(job)
            update_progress(f"✅ Processed {i+1}/{total}: {job['title']}", 50 + int((i+1)/total * 40))
            
        return analyzed_jobs
