from flask import Flask, render_template, request, Response, redirect
import sys
import time
import os
import requests
from urllib.parse import urlencode
import json
from flask_cors import CORS

with open('../metadata/config.json', 'r') as f:
    config = json.loads(f.read())

app = Flask(__name__)
CORS(app)

@app.before_request
def before_request():
    print(request.url, file=sys.stderr)
    if request.url.startswith('http://'):
        return redirect(request.url.replace('http://', 'https://'), code=301)

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

@app.route('/')
def index(name=None):
    return render_template('index.html', name=name)

@app.route('/main')
def main(name=None):
    return render_template('main.html', name=name)

@app.route('/describe_image', methods = ['POST'])
def describe_image():
    lang = request.args.get('lang')[:2]
    binary_image = request.data
    try:
        # start_time = time.time()
        result = use_describe_api(binary_image)
        result = json.loads(result)
        result = translate_text(result, lang)
        result = json.dumps(result)
        # print(time.time() - start_time, file=sys.stderr)
        # print(result, file=sys.stderr)
        return result
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 'error'
    
@app.route('/find_celebrity', methods = ['POST'])
def find_celebrity():
    binary_image = request.data
    try:
        # start_time = time.time()
        result = use_analyze_api(binary_image)
        result = json.loads(result)
        result = json.dumps(result)
        # print(time.time() - start_time, file=sys.stderr)
        # print(result, file=sys.stderr)
        return result
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 'Celebrity Not Found'


def use_describe_api(image):
    api_url = "https://koreacentral.api.cognitive.microsoft.com/vision/v2.0/describe"
    headers = {
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': config['vision_key']
    }
    params = {'maxCandidates': '1'}
    data = image

    resp = requests.post(api_url, params=params, headers=headers, data=data)
    resp.raise_for_status()
    return resp.text

def use_analyze_api(image):
    api_url = "https://koreacentral.api.cognitive.microsoft.com/vision/v2.0/analyze"
    headers = {
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': config['vision_key']
    }
    params = {
        'visualFeatures':'Categories',
        'details': 'Celebrities',
        'language': 'en'
    }
    data = image

    resp = requests.post(api_url, params=params, headers=headers, data=data)
    resp.raise_for_status()
    return resp.text

def translate_text(image_data, lang):
    result = image_data
    for i, caption in enumerate(image_data["description"]["captions"]):
        tranlated_text = use_translate_api(caption['text'], lang)
        result["description"]["captions"][i]['text'] = tranlated_text
    return result

def use_translate_api(text, lang):
    data = json.dumps([{'Text': text}])
    api_url = "https://api.cognitive.microsofttranslator.com/translate"
    headers = {
        'Ocp-Apim-Subscription-Key': config['translator_key'],
        'Content-Type': 'application/json',
        'Content-Length': str(len(data))
    }
    params = {
        'api-version':'3.0',
        'to':lang
    }

    try:
        resp = requests.post(api_url, headers=headers, params=params, data=data)
        resp.raise_for_status()
        res = json.loads(resp.text)
        return res[0]['translations'][0]['text']

    except Exception as e:
        print(str(e))
        return '번역 에러'


def make_current_time_stamp():
    return time.strftime('%y%m%d_%H%M%S')

def make_filepath(dirpath, filename):
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]
    output_file_path = dirpath + '/'
    return (output_file_path, name)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080, 
            ssl_context=('../metadata/vision_for_blind_ssl/fullchain.pem', 
                            '../metadata/vision_for_blind_ssl/privkey.pem'))