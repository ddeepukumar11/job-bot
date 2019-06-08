import dialogflow_v2 as dialogflow
import os
import requests
import json
from api_key import get_api_key, get_mongo_password
from pymongo import MongoClient
from urllib.parse import urlencode
import urllib.parse as up
from datetime import datetime

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "client-secret.json"

dialogflow_session_client = dialogflow.SessionsClient()
PROJECT_ID = "jobbot-ciuqhm"


def detect_intent_from_text(text, session_id, language_code='en'):
    session = dialogflow_session_client.session_path(PROJECT_ID, session_id)
    text_input = dialogflow.types.TextInput(
        text=text, language_code=language_code)
    query_input = dialogflow.types.QueryInput(text=text_input)
    response = dialogflow_session_client.detect_intent(
        session=session, query_input=query_input)
    return response.query_result


def get_jobs(parameters):
    #print(parameters)
    job_type = parameters.get('job_type', '')
    job_level = parameters.get('job_level', '')
    url = "https://www.themuse.com/api/public/jobs?"
    #print(job_type,job_level)
    params = {
        'category': job_type,
        'level': job_level,
        'api_key': get_api_key(),
        'page': '1',
        'descending': 'false'
    }

    #what to do
    request_url = url + urlencode(params)
    #print(request_url,'this is url')
    r = requests.get(request_url)

    results = r.json()['results'][:3]
    if not results:
          return 'No jobs for your query'
    #print(results,'*********jobs')
    data = [
        {
            'name': result['name'],
            'company': result['company']['name'],
            'link': result['refs']['landing_page']
        }
        for result in results
    ]
    saveToDatabase(data)
    return parse_dict(data)


def get_company(parameters):
    print(parameters)
    company_industry = parameters.get('company_industry', '')
    company_size = parameters.get('company_size', '')
    url = "https://www.themuse.com/api/public/companies?"

    params = {
        'industry': company_industry,
        'size': company_size,
        'api_key': get_api_key(),
        'page': '1',
        'descending': 'false'
    }

    request_url = url + urlencode(params)
    print(request_url,'this is url')
    r = requests.get(request_url)

    results = r.json()['results'][:3]
    
    if not results:
          return 'No companies for your query'
    print(results,'*********jobs')
    data = [
        {
            'name': result['name'],
            'company': result['description'],
            'link': result['refs']['landing_page']
        }
        for result in results
    ]
    saveToDatabase(data)
    return parse_dict(data)


def parse_dict(data):
      data_str = ''
      for row in data:
            data_str += "\n{}\n{}\n{}\n\n".format(row['name'],row['company'],row['link'])
      return data_str


def fetch_reply(msg, session_id):
      response = detect_intent_from_text(msg, session_id)
      # print(msg)
      # print('dflowresponse*****************',response.intent.display_name,response.parameters)

      if response.intent.display_name == "get_jobs":
          jobs = get_jobs(dict(response.parameters))
          return jobs

      elif response.intent.display_name == "get_company":
          companies = get_company(dict(response.parameters))
          return companies
      else:
          return response.fulfillment_text


client = MongoClient("mongodb+srv://ddeepukumar11:{password}@cluster0-cqdsc.mongodb.net/test?retryWrites=true&w=majority".format(
    password=up.quote(get_mongo_password())))
db = client.get_database('mydatabase')
records = db.mycollection


def saveToDatabase(msg):
    mydata = {
        'msg': msg,
        'date': str(datetime.now())
    }

    records.insert_one(mydata)
