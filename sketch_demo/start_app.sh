#!/bin/bash

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

/opt/sketch_demo/backend.py -p 8081 -d /opt/sketch_demo/models/catbus/lstm &
/opt/sketch_demo/backend.py -p 8082 -d /opt/sketch_demo/models/elephantpig/lstm &
/opt/sketch_demo/backend.py -p 8083 -d /opt/sketch_demo/models/flamingo/lstm_uncond &
/opt/sketch_demo/backend.py -p 8084 -d /opt/sketch_demo/models/owl/lstm &
/opt/sketch_demo/app.py
