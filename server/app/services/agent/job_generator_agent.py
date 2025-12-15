import json
from app.config.config import settings  # Centralized LLM and keys


# -------------------- JOB DETAIL GENERATION --------------------

def generate_job_details(summary_text: str, title: str, experience: str, location: str, employment_type: str) -> dict:
    """
    Expands HR's short summary into a complete, professional job posting using Gemini.
    """
    prompt = f"""
    You are an HR recruitment assistant. Expand the following short summary into a detailed,
    well-structured job posting in valid JSON format.

    Title: {title}
    Summary: {summary_text}
    Experience: {experience}
    Location: {location}
    Employment Type: {employment_type}

    Provide only valid JSON with this exact structure:
    {{
      "title": "",
      "description": "",
      "responsibilities": [],
      "requirements": [],
      "skills": [],
      "qualifications": [],
      "location": "",
      "employment_type": "",
      "experience": ""
    }}
    """

    response = settings.llm.invoke(prompt)
    text = response.content.strip()

    # Clean Gemini output if wrapped in code fences
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except Exception:
        return {"raw_response": text}


# -------------------- SEARCH KEYWORD GENERATION --------------------

def generate_search_keywords(job_details: dict) -> dict:
    """
    Generate LinkedIn or resume search queries & related titles using Gemini.
    """
    prompt = f"""
    You are a recruitment sourcing assistant.
    Based on the job details below, generate a professional LinkedIn search query,
    along with related job titles and recommended skills.

    Job Details:
    {json.dumps(job_details, indent=2)}

    Respond strictly in this JSON format:
    {{
      "search_query": "",
      "related_titles": [],
      "recommended_skills": []
    }}
    """

    response = settings.llm.invoke(prompt)
    text = response.content.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except Exception:
        return {"raw_response": text}
