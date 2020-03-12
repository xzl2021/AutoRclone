# -*- coding:utf-8 -*-

import sys
import os
import json
import re

for filename in os.listdir(sys.path[0] + '/accounts/'):
    obj = json.load(open(sys.path[0] + '/accounts/' + filename))
    name = re.search(r'rclone\d\d\d', obj["client_email"]).group(0)
    os.rename(sys.path[0] + '/accounts/' + filename, sys.path[0] + '/accounts/rclone-200210-' + name + '.json')
