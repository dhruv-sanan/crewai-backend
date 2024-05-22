from bs4 import BeautifulSoup
# Related third-party imports
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)


def extract_job_description(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "lxml")
    job_description_section = soup.find("section", {"class": "description"})
    job_description = job_description_section.get_text()
    job_description = job_description.strip()
    job_description = job_description.rsplit("Show more", 1)[0]
    job_title_element = soup.find_all('h1')
    job_title = job_title_element[0].text.strip()
    return job_title, job_description

@app.route('/api/extract-jd', methods=['POST'])
def extract_jd():
    data = request.get_json()
    if data is None or 'url' not in data:
        return jsonify({'error': 'Missing or invalid data'}), 400
    url = data['url']
    jt,jd = extract_job_description(url)
    if jt is None or jd is None:
        return jsonify({'error': 'Job details not found'}), 400
    return jsonify({"jt": jt, 'jd': jd})

if __name__ == '__main__':
    app.run(debug=True, port=3001)
