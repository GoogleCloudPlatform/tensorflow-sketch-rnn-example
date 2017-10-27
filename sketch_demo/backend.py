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

import base64
import cStringIO
import json
import optparse
import tempfile

from cairosvg import svg2png
from flask import Flask
from flask import request
import numpy as np
from PIL import Image
from rdp import rdp
import svgwrite
import tensorflow as tf

from magenta.models.sketch_rnn.sketch_rnn_train import *
from magenta.models.sketch_rnn.model import *
from magenta.models.sketch_rnn.utils import *
from magenta.models.sketch_rnn.rnn import *


app = Flask(__name__)


def draw_strokes(data, factor=0.12):
  with tempfile.NamedTemporaryFile() as temp_svg:
    min_x, max_x, min_y, max_y = get_bounds(data, factor)
    dims = (50 + max_x - min_x, 50 + max_y - min_y)
    dwg = svgwrite.Drawing(temp_svg.name, size=dims)
    dwg.add(dwg.rect(insert=(0, 0), size=dims, fill='white'))
    lift_pen = 1
    abs_x, abs_y = 25 - min_x, 25 - min_y
    p = 'M%s,%s ' % (abs_x, abs_y)
    command = 'm'
    for i in xrange(len(data)):
      if lift_pen == 1:
        command = 'm'
      elif command != 'l':
        command = 'l'
      else:
        command = ''
      x, y = float(data[i, 0])/factor, float(data[i, 1])/factor
      lift_pen = data[i, 2]
      p += command+str(x)+','+str(y)+' '
    the_color = 'black'
    stroke_width = 1
    dwg.add(dwg.path(p).stroke(the_color, stroke_width).fill('none'))
    dwg.save()
    temp_svg.flush()

    with tempfile.NamedTemporaryFile() as temp_png:
      svg2png(url=temp_svg.name, write_to=temp_png.name)
      image = Image.open(temp_png.name)
      image_buffer = cStringIO.StringIO()
      image.save(image_buffer, format='PNG')
      imgstr = 'data:image/png;base64,{:s}'.format(
          base64.b64encode(image_buffer.getvalue()))
  return imgstr


class SketchGenerator(object):

  def __init__(self):
    [hps_model, eval_hps_model, sample_hps_model] = load_model(MODEL_DIR)
    _ = Model(hps_model)
    eval_model = Model(eval_hps_model, reuse=True)
    sample_model = Model(sample_hps_model, reuse=True)
    sess = tf.InteractiveSession()
    sess.run(tf.global_variables_initializer())
    load_checkpoint(sess, MODEL_DIR)

    self.sess = sess
    self.eval_model = eval_model
    self.sample_model = sample_model

  def encode(self, image):

    def _compress_stroke(strokes):
      result = [[x/10.0, y/10.0, 0] for [x, y] in rdp(strokes, epsilon=1.0)]
      result[-1][2] = 1
      return result

    result = []
    strokes = []
    for i in range(0, len(image), 3):
      x, y, pen_down = image[i], image[i+1], image[i+2]
      if pen_down == 0:
        if strokes:
          result += _compress_stroke(strokes)
          strokes = [[x, y]]
      else:
        strokes.append([x, y])
    if strokes:
      result += _compress_stroke(strokes)

    pre_x, pre_y = 0, 0
    for i, (x, y, pen) in enumerate(result):
      result[i] = [x - pre_x, y - pre_y, pen]
      pre_x, pre_y = x, y

    strokes = to_big_strokes(np.array(result)).tolist()
    strokes = strokes[:MAX_SEQ_LEN+1]
    seq_len = [min(MAX_SEQ_LEN, len(result))]
    z = self.sess.run(self.eval_model.batch_z,
                      feed_dict={self.eval_model.input_data: [strokes],
                                 self.eval_model.sequence_lengths: seq_len})[0]
    return draw_strokes(to_normal_strokes(np.array(strokes))), z

  def decode(self, z_input, temperature=0.1):
    z = [z_input]
    sample_strokes, _ = sample(self.sess, self.sample_model,
                               seq_len=self.eval_model.hps.max_seq_len,
                               temperature=temperature, z=z)
    strokes = to_normal_strokes(sample_strokes)
    return draw_strokes(strokes)


@app.route('/post', methods=['POST'])
def post():
  strokes = request.get_json()
  original, z = client.encode(strokes)
  kid1 = client.decode(z, temperature=0.1)
  kid2 = client.decode(z, temperature=0.5)
  kid3 = client.decode(z, temperature=0.9)
  result = json.dumps({'kid1': kid1, 'kid2': kid2, 'kid3': kid3,
                       'original': original})
  return result


if __name__ == '__main__':

  parser = optparse.OptionParser()
  parser.add_option(
      '-p', '--port',
      type='int',
      dest='port',
      default=8081)
  parser.add_option(
      '-d', '--dir',
      type='string',
      dest='model_dir',
      default='/opt/sketch_demo/models/catbus/lstm')

  options, _ = parser.parse_args()
  port = options.port
  MODEL_DIR = options.model_dir

  with open(MODEL_DIR + '/model_config.json') as config:
    MAX_SEQ_LEN = json.load(config)['max_seq_len']

  client = SketchGenerator()
  app.run(host='127.0.0.1', port=port, debug=False)
