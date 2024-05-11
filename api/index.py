# Standard library imports
from datetime import datetime
import json
from threading import Thread
from uuid import uuid4

# Related third-party imports
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os
import requests
# Local application/library specific imports
from .crew import EmailPersonalizationCrew, HRCrew, extract_job_description
from .job_manager import append_event, jobs, jobs_lock, Event
# from utils.logging import logger
app = Flask(__name__)
CORS(app)





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
