#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from auth_decorator import requires_auth
from flask import abort
from flask import Flask
from flask import jsonify
from flask import make_response
from flask import render_template
from flask import request
import requests


app = Flask(__name__)


@app.before_request
@requires_auth
def before_request():
  pass


@app.route('/')
def canvas():
  return render_template('canvas.html')


@app.route('/post', methods=['GET', 'POST'])
def post():
  data = request.get_json()
  strokes = data['strokes']
  model = data['model']
  if not strokes:
    abort(make_response(jsonify(message='no sample'), 400))
  result = requests.post(
      'http://localhost:{}/post'.format(model_ports[model]),
      json=strokes)
  return jsonify(result.json())


if __name__ == '__main__':
  model_ports = {'catbus': 8081,
                 'elephantpig': 8082,
                 'flamingo': 8083,
                 'owl': 8084}
  app.run(host='0.0.0.0', port=80, debug=False)
