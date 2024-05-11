# Standard library imports
from bs4 import BeautifulSoup
from datetime import datetime
import json
from threading import Thread
from uuid import uuid4

# Related third-party imports
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os
import requests
from crewai import Crew
# Local application/library specific imports
# from utils.logging import logger
app = Flask(__name__)
CORS(app)

from crewai import Task



class PersonalizeEmailTask():
    def __init__(self, job_id):
        self.job_id = job_id

    def append_event_callback(self, task_output):
        # logger.info("Callback called: %s", task_output)
        append_event(self.job_id, task_output.exported_output)

    def personalize_email(self, agent, pdf_content, jd, email_template):
        return Task(
            description=f"""
                Personalize the template email for recipient using their information.

                - resume: {pdf_content}
                - job description: {jd}

                Important Info to consider:
                - When personalizing the email, first of all congratulate the 
                candidate for passing the first round of shortlisting candidates. Highlight important skills/experience which is relevant to the job.
                    And make sure to incorporate it naturally into the email.  without going too much in to detail.
                - Make sure to keep the updated email roughly the same same length as the template email.
                - Make sure you select the job title, the name of the comapny, name of the candidate and other necessary details from the {jd}
                The template email is as follows:

                ```
                {email_template}
                ```
            """,
            agent=agent,
            expected_output=f"Personalized email draft.",
            async_execution=True,
        )

    def ghostwrite_email(self, agent, draft_email):
        return Task(
            description=f"""
                Revise the draft email to adopt the following writing style.

                Writing Style:
                - Use a more formal, engaging, and slightly happy tone, mirroring ghost writer's final email communication style. 
                - This approach prioritizes clear, direct communication while maintaining a friendly and approachable tone. 
                - Use straightforward language, including phrases like "Hey [Name]!" to start emails or messages and end with "Regards". 
                - The tone will be optimistic and encouraging, aiming to build rapport and motivate action, while staying grounded in practical advice.

                Important Notes:
                - Do not use emojis.
            """,
            agent=agent,
            context=[draft_email],
            expected_output=f"A revised email draft in ghost writer's specified tone and style.",

        )


class HRTask():
    def __init__(self, job_id):
        self.job_id = job_id

    def append_event_callback(self, task_output):
        # logger.info("Callback called: %s", task_output)
        append_event(self.job_id, task_output.exported_output)

    def scoreHR(self, agent, pdf_content, jd):
        return Task(
            description=f"""
                provide a score indicating the suitability of the candidate for the specified role.


                - resume: {pdf_content}
                - job description: {jd}

                Important Info to consider:
                - Make sure you compare and contrast the skills required in {jd} and the skills present in {pdf_content}
                - Make sure you compare and contrast the experience required in {jd} and the skills present in {pdf_content}
                - After carefull accessment of both the things, then you give a score for the CV (from 1 to 10)
            """,
            agent=agent,
            expected_output=f"the score indicating the suitability of the candidate for the specified role",
        )

    def explainHR(self, agent, score):
        return Task(
            description=f"""
                provide an explaination indicating the suitability of the candidate for the specified role.

                Important Info to consider:
                - Make sure you compare and contrast the skills required in job description and the skills present in resume.
                - Make sure you compare and contrast the experience required in job description and the skills present in resume.
                - After carefull accessment of both the things, then you give an explanation of the {score}
                - the explaination should be 2-4 sentences long. Not more than 4 sentences.

            """,
            agent=agent,
            expected_output=f"an explaination indicating the suitability of the candidate for the specified role",
            context=[score],
        )

    # def ghostwrite_explainHR(self, agent, explaination):
    #     return Task(
    #         description=f"""
    #             Revise the explaination to adopt the following writing style.

    #             Writing Style:
    #             - Use a more formal, engaging, and slightly honest tone, mirroring ghost writer's final email communication style.
    #             - This approach prioritizes clear, direct communication while maintaining a friendly and approachable tone.
    #             - Use straightforward language.
    #             - The tone will be optimistic and encouraging, aiming to build rapport and motivate action, while staying grounded in the honest review of the CV.

    #             Important Notes:
    #             - Do not use emojis.
    #         """,
    #         agent=agent,
    #         context=[explaination],
    #         expected_output=f"A revised explaination in ghost writer's specified tone and style.",

    #     )


from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict
from threading import Lock
# from utils.logging import logger

jobs_lock = Lock()
jobs: Dict[str, "Job"] = {}


@dataclass
class Event:
    timestamp: datetime
    data: str


@dataclass
class Job:
    status: str
    events: List[Event]
    result: str


def append_event(job_id: str, event_data: str):
    with jobs_lock:
        if job_id not in jobs:
            # logger.info("Job %s started", job_id)
            jobs[job_id] = Job(
                status='STARTED',
                events=[],
                result='')
        else:
            # TODO ADD logger
            print("Appending event for job %s: %s", job_id, event_data)
        jobs[job_id].events.append(
            Event(timestamp=datetime.now(), data=event_data))

from crewai import Agent
from langchain_groq import ChatGroq
import os

class EmailPersonalizationAgents():
    def __init__(self):
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="mixtral-8x7b-32768"
        )

        # self.llm = ChatOpenAI(
        #     model="gpt-3.5-turbo",
        #     api_key=os.getenv("OPENAI_API_KEY")
        # )

    def personalize_email_agent(self):
        return Agent(
            role="Email Personalizer",
            goal=f"""
                Personalize template emails for candidates that have been selected for the interview stage.

                Given a template email and recipient information (name, email, resume), 
                personalize the email by incorporating the recipient's details 
                into the email while maintaining the core message and structure of the original email. 
                This involves updating the introduction, body, and closing of the email to make 
                it more personal and engaging for each recipient. Make sure to congratulate the 
                candidate for passing the first round of shortlisting candidates.
                """,
            backstory="""
                As an Email Personalizer, you are responsible for customizing template emails for individual recipients based on their information.
                """,
            verbose=True,
            llm=self.llm,
            max_iter=2,
        )

    def ghostwriter_agent(self):
        return Agent(
            role="Ghostwriter",
            goal=f"""
                Revise draft emails to adopt the Ghostwriter's writing style.

                Use an formal, engaging, and slightly corporate tone, mirroring the Ghostwriter's final email communication style.
                """,
            backstory="""
                As a Ghostwriter, you are responsible for revising draft emails to match the Ghostwriter's writing style, focusing on clear, direct communication with a formal, approachable and slightly happy tone.
                """,
            verbose=True,
            llm=self.llm,
            max_iter=2,
        )


class HRAgents():

    def __init__(self):
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="mixtral-8x7b-32768"
        )
        # self.llm = ChatOpenAI(
        #     model="gpt-3.5-turbo",
        #     api_key=os.getenv("OPENAI_API_KEY")
        # )

    def scoreHR_agent(self) -> Agent:
        return Agent(
            role="Human Resource Manager",
            goal=f"""provide a score indicating the suitability of the candidate for the specified role

                Important:
                - The final result must include the score that you have decided to give. Do not give anything else than the score.
                - You have give a score for the CV (from 1 to 10). Do not give less than 1 and more than 10.
                - Do not generate fake scroe. 
                - Return the appropriate score which genuinely matches the resume with job description.
                - Make sure your score should reflect how much suitable is the candidate for the job.
                """,
            backstory="""As a Human Resource Manager, you are responsible for giving a score to the resume according to the job description of the role required in the company.""",
            llm=self.llm,
            verbose=True,
            max_iter=2,
        )

    def explainHR_agent(self) -> Agent:
        return Agent(
            role="Human Resource Manager",
            goal="""provide an explaination indicating the suitability of the candidate for the specified role.""",
            backstory="""As a Human Resource Manager, you are responsible to explaination indicating the suitability of the candidate for the specified role required
                within the company and gathering relevant information.
 
                Important Info to consider:
                - Make sure you compare and contrast the skills required in job description and the skills present in resume
                - Make sure you compare and contrast the experience required in job description and the skills present in resume
                - After carefull accessment of both the things, then you give an explanation of the score
                - the explaination should be 2-4 sentences long. Not more than 4 
                """,
            llm=self.llm,
            verbose=True,
            max_iter=2,)

    # def ghostwrite_explainHR_agent(self):
    #     return Agent(
    #         role="Ghostwriter",
    #         goal=f"""
    #             Revise explainations to adopt the Ghostwriter's writing style.

    #             Use an formal, engaging, and slightly corporate tone, mirroring the Ghostwriter's final email communication style.
    #             """,
    #         backstory="""
    #             As a Ghostwriter, you are responsible for revising explainations to match the Ghostwriter's writing style,
    #             focusing on clear, direct communication with a formal, approachable and slightly honest tone.
    #             """,
    #         verbose=True,
    #         llm=self.llm,
    #         max_iter=2,
    #     )


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


def extract_job_description(url):
    response = requests.get(url)
    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")
    job_description_section = soup.find("section", {"class": "description"})
    job_description = job_description_section.get_text()
    job_description = job_description.strip()
    return job_description


@app.route('/api/extract-jd', methods=['POST'])
def extract_jd():
    data = request.get_json()
    if data is None or 'url' not in data:
        return jsonify({'error': 'Missing or invalid data'}), 400
    url = data['url']
    jd = extract_job_description(url)
    parts = jd.rsplit("Roles", 1)
    jt = parts[0]
    jd = parts[1].rsplit("Show more", 1)[0]
    return jsonify({"jt": jt, 'jd': jd})

from io import BytesIO
from PyPDF2 import PdfReader

def input_pdf_text(url):
    try:
        response = requests.get(url, allow_redirects=True)
        response.raise_for_status()  # Raise error for non-2xx status codes

        if response.content:
            # Use BytesIO to handle the PDF content in memory
            with BytesIO(response.content) as pdf_file:
                reader = PdfReader(pdf_file)
                text = ""
                for page in range(len(reader.pages)):
                    page = reader.pages[page]
                    # Handle newlines and extra spaces
                    text += " " + page.extract_text().replace('\n', ' ').strip()
                return text.strip()
        else:
            return "Error: Empty response from URL"

    except requests.exceptions.RequestException as e:
        print(f"Error fetching PDF: {e}")
        return "Error: Failed to retrieve PDF"
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return "Error: An error occurred while processing the PDF"
    

@app.route('/api/extract-text', methods=['POST'])
def extract_text():
    data = request.get_json()
    if data is None or 'url' not in data:
        return jsonify({'error': 'Missing or invalid data'}), 400
    pdf_url = data['url']
    extracted_text = input_pdf_text(pdf_url)
    return jsonify({'text': extracted_text})


def kickoff_crewpdf(job_id, pdf_content, jd):
    results = None
    try:
        Email_Personalization_Crew = EmailPersonalizationCrew(job_id)
        Email_Personalization_Crew.setup_crew(
            pdf_content, jd)
        results = Email_Personalization_Crew.kickoff()
        # logger.info(f"Crew for job {job_id} is complete", results)

    except Exception as e:
        # logger.error(f"Error in kickoff_crew for job {job_id}: {e}")
        append_event(job_id, f"An error occurred: {e}")
        with jobs_lock:
            jobs[job_id].status = 'ERROR'
            jobs[job_id].result = str(e)

    with jobs_lock:
        jobs[job_id].status = 'COMPLETE'
        jobs[job_id].result = results
        jobs[job_id].events.append(
            Event(timestamp=datetime.now(), data="Crew complete"))


def kickoff_crewHR(job_id, pdf_content, jd):
    results = None
    try:
        HRcrew = HRCrew(job_id)
        HRcrew.setup_crew(
            pdf_content, jd)
        results = HRcrew.kickoff()
        # logger.info(f"Crew for job {job_id} is complete", results)

    except Exception as e:
        # logger.error(f"Error in kickoff_crew for job {job_id}: {e}")
        append_event(job_id, f"An error occurred: {e}")
        with jobs_lock:
            jobs[job_id].status = 'ERROR'
            jobs[job_id].result = str(e)

    with jobs_lock:
        jobs[job_id].status = 'COMPLETE'
        jobs[job_id].result = results
        jobs[job_id].events.append(
            Event(timestamp=datetime.now(), data="Crew complete"))


@app.route("/api/crewpdf", methods=["POST"])
def run_crewpdf():
    data = request.json

    job_id = str(uuid4())
    pdf_content = data['pdf_content']
    jd = data['jt']
    jd = data['jd']
    thread = Thread(target=kickoff_crewpdf, args=(
        job_id, pdf_content, jd))
    thread.start()
    return jsonify({"job_id": job_id}), 202


@app.route("/api/crewHR", methods=["POST"])
def run_crewHR():
    data = request.json
    job_id = str(uuid4())
    pdf_content = data['pdf_content']
    jd = data['jd']
    thread = Thread(target=kickoff_crewHR, args=(
        job_id, pdf_content, jd))
    thread.start()
    return jsonify({"job_id": job_id}), 202


@app.route("/api/crew/<job_id>", methods=["GET"])
def get_status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            abort(404, description="Job not found")

     # Parse the job.result string into a JSON object
    try:
        result_json = job.result
    except json.JSONDecodeError:
        # If parsing fails, set result_json to the original job.result string
        result_json = job.result

    return jsonify({
        "job_id": job_id,
        "status": job.status,
        "result": result_json,
        "events": [{"timestamp": event.timestamp.isoformat(), "data": event.data} for event in job.events]
    })
