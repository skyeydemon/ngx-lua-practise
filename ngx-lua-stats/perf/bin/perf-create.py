#!/bin/env python

import urllib2, urllib
import json, sys, time, re, os
from lhip import *
from perf_log import *

HTTP_404_ERROR = 'HTTP Error 404: Not Found'
CREATE_STR = """echo  "create {endpoint} {counter} `date '+%s'` {value} COUNTER" | nc perfcounter.miliao.srv 4444"""

class HostData():
  def __init__(self, host_lst = []):
    self.host_lst = host_lst
    self.index = 0
  
  def get_json(self, endpoint):
    js, js_, url = None, {}, '''http://%s/status ''' %(endpoint)
    try:
      js = urllib2.urlopen(url).read()
      js_ = json.loads(js)
    except Exception, e:
      if str(e) == HTTP_404_ERROR:
        js_ = None
      else:
        if js != None:
          for i in js.split('key: '):
            if i != '':
              k, v, nil = i.split('\n')
              js_[k] = v
        else:
          js_ = None
    logger.info("[%s] Receive %s from host %s", __file__, str(js_), \
            self.host_lst[self.index])

    return endpoint, js_

  def __iter__(self):
    return self

  def next(self):
    try:
      endpoint, res = self.get_json(self.host_lst[self.index])
    except IndexError:
      raise StopIteration
    self.index += 1
    return endpoint, res


if __name__ == "__main__":
  hd = HostData(main())

  for e, res in hd:
    if res is not None:
      for k, v in res.items():
#        print PUSH_STR.format(endpoint = e, counter = k, value = v)
        result = os.system(CREATE_STR.format(endpoint = e, counter = k, value = v))
        logger.info("[%s] Exec %s and result %s", __file__,\
                CREATE_STR.format(endpoint = e, counter = k, value = v), result)
