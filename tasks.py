from crewai import Task
from crewai import Task, Agent
from textwrap import dedent


from job_manager import append_event
# from utils.logging import logger
from models import EmailInfo, ScoreInfo


class PersonalizeEmailTask():
    def __init__(self, job_id):
        self.job_id = job_id

    def append_event_callback(self, task_output):
        # logger.info("Callback called: %s", task_output)
        append_event(self.job_id, task_output.exported_output)

    def personalize_email(self, agent: Agent, pdf_content: str, jt: str, jd: str, email_template):
        return Task(
            description=f"""
                Personalize the template email for recipient using their information.

                - resume: {pdf_content}
                - Job title: {jt}
                - job description: {jd}

                Important Info to consider:
                - When personalizing the email, first of all congratulate the 
                candidate for passing the first round of shortlisting candidates. Highlight important skills/experience which is relevant to the job.
                    And make sure to incorporate it naturally into the email without going too much in to detail.
                - Make sure to keep the updated email roughly the same same length as the template email.
                - Make sure you select the job title, the name of the comapny, name of the candidate and other necessary details from the job description.
                - Make sure you output a JSON object containing subject and content of the email.
                Writing Style:
                - Use a more formal, engaging, and slightly happy tone, mirroring ghost writer's final email communication style. 
                - This approach prioritizes clear, direct communication while maintaining a friendly and approachable tone. 
                - Use straightforward language, including phrases like "Hey [Name]!" to start emails or messages and end with "Regards, [Company Name]". 
                - The tone will be optimistic and encouraging, aiming to build rapport and motivate action, while staying grounded in practical advice.
                - Make sure you output a JSON object containing subject and content of the email.
                Important Notes:
                - Do not use emojis.
                The template email is as follows:

                ```
                {email_template}
                ```
            """,
            agent=agent,
            expected_output=f"A JSON object containing subject and content of the personalized email draft",
            callback=self.append_event_callback,
            output_json=EmailInfo,
        )

    def ghostwrite_email(self, agent: Agent, draft_email: Task):
        return Task(
            description=f"""
                Revise the draft email to adopt the following writing style.

                Writing Style:
                - Use a more formal, engaging, and slightly happy tone, mirroring ghost writer's final email communication style. 
                - This approach prioritizes clear, direct communication while maintaining a friendly and approachable tone. 
                - Use straightforward language, including phrases like "Hey [Name]!" to start emails or messages and end with "Regards". 
                - The tone will be optimistic and encouraging, aiming to build rapport and motivate action, while staying grounded in practical advice.
                - Make sure you output a JSON object containing subject and content of the email.
                Important Notes:
                - Do not use emojis.
            """,
            agent=agent,
            context=[draft_email],
            expected_output=f"A JSON object containing subject and content of the revised email draft in ghost writer's specified tone and style.",
            callback=self.append_event_callback,
            output_json=EmailInfo

        )


class Score_Task():
    def __init__(self, job_id):
        self.job_id = job_id

    def append_event_callback(self, task_output):
        # logger.info("Callback called: %s", task_output)
        append_event(self.job_id, task_output.exported_output)

    def score_person_task(self, agent, pdf_content, jd, jt):
        return Task(
            description=f"""
                provide a score indicating the suitability of the candidate for the specified role.


                - resume: {pdf_content}
                - job description: {jd}
                - job title: {jt}

                Important Info to consider:
                - Make sure you compare and contrast the skills andexperience required in job description and the skills present in resume
                - After carefull accessment of both the things, then you give a score for the CV (from 1 to 10)
                - Make sure your explanation is no longer than 5 sentences
                - Make sure you output a JSON object containing score and explanation of that score
            """,
            agent=agent,
            expected_output=f"A JSON object containing score and explanation of that score",
            callback=self.append_event_callback,
            output_json=ScoreInfo,
        )

    def explainHR(self, agent, score):
        return Task(
            description=f"""
                provide an explanation indicating the suitability of the candidate for the specified role.

                Important Info to consider:
                - Make sure you compare and contrast the skills required in job description and the skills present in resume.
                - Make sure you compare and contrast the experience required in job description and the skills present in resume.
                - After carefull accessment of both the things, then you give an explanation of the {score}
                - the explanation should be 2-4 sentences long. Not more than 4 sentences.

            """,
            agent=agent,
            expected_output=f"an explanation indicating the suitability of the candidate for the specified role",
            context=[score],
        )

    # def ghostwrite_explainHR(self, agent, explanation):
    #     return Task(
    #         description=f"""
    #             Revise the explanation to adopt the following writing style.

    #             Writing Style:
    #             - Use a more formal, engaging, and slightly honest tone, mirroring ghost writer's final email communication style.
    #             - This approach prioritizes clear, direct communication while maintaining a friendly and approachable tone.
    #             - Use straightforward language.
    #             - The tone will be optimistic and encouraging, aiming to build rapport and motivate action, while staying grounded in the honest review of the CV.

    #             Important Notes:
    #             - Do not use emojis.
    #         """,
    #         agent=agent,
    #         context=[explanation],
    #         expected_output=f"A revised explanation in ghost writer's specified tone and style.",

    #     )
