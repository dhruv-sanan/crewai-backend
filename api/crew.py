from agents import EmailPersonalizationAgents, HRAgents
from job_manager import append_event
from tasks import PersonalizeEmailTask, HRTask
from crewai import Crew


class EmailPersonalizationCrew:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.crew = None

    def setup_crew(self, pdf_content, jd):
        agents = EmailPersonalizationAgents()
        tasks = PersonalizeEmailTask(
            job_id=self.job_id)

        personalize_email_agent = agents.personalize_email_agent()
        ghostwriter_agent = agents.ghostwriter_agent()
        email_template = """
                            Dear [Candidate Name],

                            We are pleased to inform you that you have successfully progressed to the next round of interviews for the [Job Title] position at [Company Name].
                            We were impressed with your performance and qualifications during the first round, and we are eager to learn more about you.
                            The next round will consist of an in-person interview with the team. We will be in touch shortly to schedule a convenient time for you.
                            In the meantime, feel free to review the job description again and prepare any questions you may have for us.
                            We look forward to meeting with you again soon!

                            Regards,
                            ALINDOR
                        """
        personalize_email = tasks.personalize_email(
            personalize_email_agent, pdf_content, jd, email_template)
        ghostwrite_email = tasks.ghostwrite_email(
            ghostwriter_agent, personalize_email)

        # Setup Crew
        self.crew = Crew(
            agents=[
                personalize_email_agent, ghostwriter_agent
            ],
            tasks=[
                personalize_email, ghostwrite_email
            ],
            max_rpm=29
        )

    def kickoff(self):
        if not self.crew:
            append_event(self.job_id, "Crew not set up")
            return "Crew not set up"

        append_event(self.job_id, "Task Started")
        try:
            results = self.crew.kickoff()
            append_event(self.job_id, "Task Complete")
            return results
        except Exception as e:
            append_event(self.job_id, f"An error occurred: {e}")
            return str(e)


class HRCrew:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.crew = None

    def setup_crew(self, pdf_content, jd):
        agents = HRAgents()
        tasks = HRTask(
            job_id=self.job_id)

        score_HR_agent = agents.scoreHR_agent()
        # explain_HR_agent = agents.explainHR_agent()
        # ghostwrite_explainHR_agent = agents.ghostwrite_explainHR_agent()
        score_HR = tasks.scoreHR(
            score_HR_agent, pdf_content, jd)
        # explain_HR = tasks.explainHR(
        #     explain_HR_agent, score_HR)
        # ghostwrite_explainHR = tasks.ghostwrite_explainHR(
        #     ghostwrite_explainHR_agent, explainHR)

        # Setup Crew
        self.crew = Crew(
            agents=[
                score_HR_agent
            ],
            tasks=[
                score_HR
            ],
            max_rpm=29
        )

    def kickoff(self):
        if not self.crew:
            append_event(self.job_id, "Crew not set up")
            return "Crew not set up"

        append_event(self.job_id, "Task Started")
        try:
            results = self.crew.kickoff()
            append_event(self.job_id, "Task Complete")
            return results
        except Exception as e:
            append_event(self.job_id, f"An error occurred: {e}")
            return str(e)
