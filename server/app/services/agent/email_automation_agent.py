import os
from app.config.config import settings
from app.repository.match_result_repository import MatchResultRepository
from app.repository.resume_repository import ResumeRepository
from app.repository.job_repository import JobRepository
from app.services.utils.email_utils import send_email_smtp
from app.services.utils.log import logger


class EmailAutomationService:

    @staticmethod
    async def generate_email_draft(status: str, candidate_name: str, job_title: str, match_link: str):
        """
        Uses configured Gemini model from settings to generate a personalized email draft.
        """
        prompt = f"""
        You are an HR assistant writing professional emails.
        Generate an email for candidate **{candidate_name}** regarding the job **{job_title}**.
        The hiring decision is **{status}**.
        Include:
        - A warm, personalized message.
        - Mention the candidate's name and job title.
        - Add a link to view their match analysis: {match_link}.
        - Keep it under 200 words.
        """

        try:
            # ✅ Use globally configured Gemini model from settings
            response = settings.llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            logger.error(f"Gemini email draft generation failed: {str(e)}")
            return (
                f"Dear {candidate_name},\n\n"
                f"We wanted to inform you about your {status} status for {job_title}.\n"
                f"Please check your match details here: {match_link}.\n\n"
                f"Best regards,\nHR Team"
            )

    # --------------------------------------------------------------------
    @staticmethod
    async def send_candidate_status_email(match_result_id: str, status: str):
        """
        Generates and sends AI-drafted emails to candidates based on status update.
        """
        # ✅ Step 1: Fetch match result from DB
        match_result = await MatchResultRepository.find_by_id(match_result_id)
        if not match_result:
            logger.error(f"No match result found for ID: {match_result_id}")
            return {"success": False, "message": "Match result not found"}

        # ✅ Step 2: Fetch related resume and job details
        resume = await ResumeRepository.find_by_id(match_result.get("resume_id"))
        job = await JobRepository.find_by_id(match_result.get("job_id"))

        if not resume:
            logger.error(f"Resume not found for match result ID {match_result_id}")
            return {"success": False, "message": "Resume not found"}
        if not job:
            logger.error(f"Job not found for match result ID {match_result_id}")
            return {"success": False, "message": "Job not found"}

        # ✅ Extract candidate info
        candidate_email = (
            resume.get("parsed_data", {}).get("email")
            or resume.get("email")
            or None
        )
        candidate_name = (
            resume.get("parsed_data", {}).get("name")
            or resume.get("file_name", "Candidate")
        )
        job_title = job.get("title", "the applied position")

        if not candidate_email:
            logger.warning(f"No candidate email found in resume for match result ID {match_result_id}")
            return {"success": False, "message": "Candidate email not found"}

        # ✅ Step 3: Build match result link (frontend)
        match_link = f"{settings.FRONTEND_URL}/candidate/match/{match_result_id}"

        # ✅ Step 4: Generate email content using Gemini
        email_body = await EmailAutomationService.generate_email_draft(
            status=status,
            candidate_name=candidate_name,
            job_title=job_title,
            match_link=match_link
        )

        # ✅ Step 5: Send the email
        subject = f"Your Application Update for {job_title}"
        send_email_smtp(to_email=candidate_email, subject=subject, body=email_body)

        logger.info(f"✅ Email sent to {candidate_email} for status: {status}")
        return {"success": True, "message": f"Email sent to {candidate_email} for status '{status}'"}
