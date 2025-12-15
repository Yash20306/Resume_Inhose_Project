import os
import requests
from app.config.config import settings
from app.services.agent.resume_parser_agent import (
    parse_resume_with_gemini,
    check_match,
    extract_text_from_pdf,
    extract_text_from_docx,
)
from app.services.utils.log import logger


# -------------------- LOCAL CANDIDATE MATCHING --------------------

def find_local_candidates(job_details: dict, resumes_folder: str = "uploads/resumes") -> list:
    """
    Matches resumes stored locally against the provided job details.

    Args:
        job_details (dict): Must contain at least a 'description'.
        resumes_folder (str): Folder path containing resume files.

    Returns:
        list: Local candidate matches with parsed resume and match result.
    """
    matched = []

    if not os.path.exists(resumes_folder):
        logger.warning(f"⚠️ Resumes folder not found: {resumes_folder}")
        return matched

    for file_name in os.listdir(resumes_folder):
        if not file_name.lower().endswith((".pdf", ".docx")):
            continue

        file_path = os.path.join(resumes_folder, file_name)

        try:
            # Extract resume text
            text = (
                extract_text_from_pdf(file_path)
                if file_name.lower().endswith(".pdf")
                else extract_text_from_docx(file_path)
            )

            # Parse and match
            parsed_resume = parse_resume_with_gemini(text)
            match_result = check_match(job_details.get("description", ""), parsed_resume)

            matched.append({
                "source": "local",
                "file_name": file_name,
                "parsed_resume": parsed_resume,
                "match_result": match_result
            })

            logger.info(f"✅ Local resume processed successfully: {file_name}")

        except Exception as e:
            logger.error(f"❌ Error processing local resume {file_name}: {e}")

    return matched


# -------------------- GLOBAL CANDIDATE SEARCH (Apollo.io) --------------------

def find_candidates_via_apollo(job_details: dict, top_n: int = 5) -> list:
    """
    Fetches global candidates from Apollo.io Contact Search API (Free Tier compatible).
    Returns dynamic search results — does not save anything locally.

    Args:
        job_details (dict): Must contain 'title', 'skills', or 'description'.
        top_n (int): Number of top global candidates to fetch.

    Returns:
        list: Candidate profiles from Apollo (LinkedIn, email, title, etc.)
    """
    api_key = settings.APOLLO_API_KEY
    if not api_key:
        logger.error("⚠️ Apollo API key missing in environment (.env)")
        return []

    search_url = "https://api.apollo.io/v1/contacts/search"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }

    title = job_details.get("title", "")
    location = job_details.get("location", "")
    skills = ", ".join(job_details.get("skills", []))
    description = job_details.get("description", "")

    # Build query for Apollo free-tier search
    query_text = f"{title} {skills} {description}".strip()

    payload = {
        "q_keywords": query_text,
        "person_locations": [location] if location else [],
        "page": 1,
        "limit": top_n,
    }

    try:
        response = requests.post(search_url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()

        results = []
        for contact in data.get("contacts", []):
            results.append({
                "source": "global",
                "name": contact.get("name"),
                "title": contact.get("title"),
                "linkedin_url": contact.get("linkedin_url"),
                "email": contact.get("email"),
                "organization": contact.get("organization", {}).get("name"),
                "location": contact.get("city") or contact.get("state") or "N/A",
            })

        logger.info(f"🌍 Apollo global candidates fetched: {len(results)} found.")
        return results

    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ Apollo API HTTP error {e.response.status_code}: {e.response.text}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Apollo network error: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ Unexpected Apollo processing error: {e}")
        return []


# -------------------- MAIN CANDIDATE FINDER PIPELINE --------------------

def find_candidates(
    job_details: dict,
    resumes_folder: str = "uploads/resumes",
    global_search: bool = False,
    top_n: int = 5
) -> list:
    """
    Finds top candidates for a given job — locally and optionally via Apollo API.

    Args:
        job_details (dict): Job description, title, or skill-based details.
        resumes_folder (str): Folder path containing resumes.
        global_search (bool): Enable Apollo-based search if True.
        top_n (int): Number of top candidates to return overall.

    Returns:
        list: Sorted list of local and/or global candidates.
    """
    all_candidates = []

    # ✅ Local Matches
    local_matches = find_local_candidates(job_details, resumes_folder)
    all_candidates.extend(local_matches)

    # ✅ Global Matches (Dynamic API — not stored)
    if global_search:
        apollo_matches = find_candidates_via_apollo(job_details, top_n)
        all_candidates.extend(apollo_matches)

    # ✅ Sort by match quality for local resumes only
    all_candidates.sort(
        key=lambda x: (
            1 if isinstance(x.get("match_result", {}), dict)
            and x["match_result"].get("status") == "pass"
            else 0
        ),
        reverse=True
    )

    logger.debug(f"🎯 Total candidates retrieved: {len(all_candidates)}")
    return all_candidates[:top_n]
