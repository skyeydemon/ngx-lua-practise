#!/bin/env python
#-*- coding:utf-8 -*-
import urllib2
import json
import os
import sys
import time
import cPickle as pickle
from hashlib import md5
import traceback
import logging

BASE_DIR = "/".join(os.path.abspath(__file__).split("/")[0:-2])
DATA_DIR = BASE_DIR + "/data/"
LOG_DIR = BASE_DIR + "/log/"
CONF_DIR = BASE_DIR + "/conf/"
CONF_FILE = CONF_DIR + "perf_conf.py"


if not os.path.isfile(CONF_FILE):
  print "%s not found. Example:"%(CONF_FILE)
  print '''
#!/bin/env python\n
#-*- coding:utf-8 -*-\n

## tag_string和对应的group\n
tag_group = {"cop.xxxx_owt.xxx_pdl.com_srv.l7_idc.sd,idc.lg_grp.pub,grp.pay":["xxx-l7",":8080/status",":8080"]}\n
## xperf服务器的地址\n
xperf_uri = "10.0.4.65:8088/ez"'''
  sys.exit(0)

if not os.path.exists(DATA_DIR):
  os.system("mkdir -p %s" %DATA_DIR)
if not os.path.exists(LOG_DIR):
  os.system("mkdir -p %s" %LOG_DIR)

ISOTIMEFORMAT = '%Y%m%d'
TODAY = time.strftime(ISOTIMEFORMAT,time.localtime(time.time()))
NOW_M = time.strftime('%M',time.localtime(time.time()))

log_file = LOG_DIR + "fuck_perf.log." + TODAY
logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s %(message)s')
logger = logging.getLogger()

##########################################################
#### 需要配置项目
## tag_string和对应的group
#tag_group = {"cop.xxxx_owt.xxx_pdl.com_srv.l7_idc.sd,idc.lg_grp.pub,grp.pay":["xxx-l7",":8080/status",":8080"]}
## xperf服务器的地址
#xperf_uri = "10.0.4.65:8088/ez"

##########################################################

def get_json(url):

  try:

    url = "http://%s"%(url)
    ## 用来存储一些信息
    status_dict = {}
    cal_dict = {}
    status_list = []
    site_list = []

    js = urllib2.urlopen(url).read().split("\n")
    for i in js:
      if i:
        _d = json.loads( i)
        for k,v in _d.items():
          ## 如果字典的k v 有空值则直接抛弃
          if not k or not v:
            pass
          else:
            tlist = k.split("__")
            ## 检查k是否是以 __ 分割的
            if len(tlist) == 2:
              if tlist[0] not in site_list:
                ## 顺便将site项目拿出来,单独放到一个list中
	            site_list.append( str(tlist[0]) )

              site = str(tlist[0])
              counter = str(tlist[1])
              value = float(v)

              ## 将数据拆分放入list中
              _list = [ site, counter, value ]
              status_list.append(_list)

              status_dict.update( {str(k) : float(v)} )
              ## 生成一个比较复杂的字典
              if cal_dict.has_key(site):
                cal_dict[site].update( {counter : value} )
              else:
                cal_dict.update( {site : {counter : value} } )

    #return status_dict, site_list, status_list, cal_dict
    return cal_dict
  except Exception, e:
    logger.info ("Get %s stauts error. %s" %( url, e) )


def save_cache_by_arith(obj, url, interval):
  ## 通过对当前分钟取余数来区分不同的历史数据, 并且将其通过pickle持久化
  arithmetic = int(NOW_M) % interval
  url_md5 = md5(url).hexdigest()
  cache_file = "%s/%s.cache.%s" %(DATA_DIR, url_md5, arithmetic)
  logger.info("Save to:%s" %cache_file)
  f = open(cache_file, "w+")
  pickle.dump(obj, f)
  f.close()


def load_cache_by_file(file_path):
  ## 通过指定文件路径来load一个pickle数据
  logger.info("Load from:%s" %file_path)
  if os.path.exists(file_path):
    f = open(file_path, 'rb')
    try:
      r = pickle.load(f)
    except Exception, e:
      logger.info("Load file %s error : %s" %( file_name, e))
      return {}
    finally:
      f.close()
    return r
  return {}


def cal_delta_dict(dict1 , dict2):
  # 将两个字典里面的相同项算出delta并且存在同样结构的字典中输出
  # detal是用dict2 减去 dict1 
  try:
    delta_d = {}
    for site, c_dict1 in dict1.items():
      delta_d[site] = {}
      if not dict2.has_key(site):
        pass
      c_dict2 = dict2[site]
      for counter, value in c_dict1.items():
        if not c_dict2.has_key(counter):
          pass
        delta_v = c_dict2[counter] - c_dict1[counter]
        ## 如果得到的detal小于0则不作为结果
        if float(delta_v) < 0:
          logger.info("Delta dict %s and %s lt 0! %s - %s = %s" % ( dict1, dict2, c_dict2[counter], c_dict2[counter], delta_v))
          delta_v = 0
        else:
          delta_d[site].update( {counter:delta_v } )
    logger.info("Delta dict : %s"%(delta_d))
    return delta_d
  except Exception, e:
    logger.info("Delta dict %s and %s  error. %s"  %( dict1, dict2, e) )
    return {}


def send_counter_by_part( now_dict, delta_dict):
  SEND_LIST = []
  ## 有的数据需要发送原值，有的需要将delta进行计算之后发送
  ## 先处理现有counter上报的值
  COUNTER_TYPE_LIST = ['status_code_4xx_counter','status_code_5xx_counter','query_counter','bytes_sent_counter']
  for site,c_dict_n in now_dict.items():
    for COUNTER_TYPE in COUNTER_TYPE_LIST:
      if c_dict_n.has_key(COUNTER_TYPE):
        if float(c_dict_n[COUNTER_TYPE]) >0:
          counter_name = site + "__" + COUNTER_TYPE
          counter_value = int(c_dict_n[COUNTER_TYPE])
          SEND_DATA = ["COUNTER", counter_name, counter_value]
          SEND_LIST.append(SEND_DATA)
  
  ## 处理需要做计算的数据
  for site,c_dict_d in delta_dict.items():
    ## 计算speed平均值
    if c_dict_d.has_key("query_counter") and c_dict_d.has_key("bytes_sent_counter"):
      if float(c_dict_d["query_counter"]) > 0:
        speed_avg = c_dict_d["bytes_sent_counter"] / c_dict_d["query_counter"]
        if float(speed_avg) > 0:
          counter_name = site + "__" + "speed_avg"
          SEND_DATA = ["GAUGE", counter_name, speed_avg]
          SEND_LIST.append(SEND_DATA)
    ## 计算request_time平均值
    if c_dict_d.has_key("query_counter") and c_dict_d.has_key("request_time_counter"):
      if float(c_dict_d["query_counter"]) >0:
        request_time_avg = c_dict_d["request_time_counter"] / c_dict_d["query_counter"]
        if float(request_time_avg) > 0:
          counter_name = site + "__" + "request_time_avg"
          SEND_DATA = ["GAUGE", counter_name, request_time_avg]
          SEND_LIST.append(SEND_DATA)
    ## 计算upstream_time平均值
    if c_dict_d.has_key("query_counter") and c_dict_d.has_key("upstream_time_counter"):
      if float(c_dict_d["query_counter"]) >0:
        upstream_time_avg =  c_dict_d["upstream_time_counter"] / c_dict_d["query_counter"]
        if float(upstream_time_avg) > 0:
          counter_name = site + "__" + "upstream_time_avg"
          SEND_DATA = ["GAUGE", counter_name, upstream_time_avg]
          SEND_LIST.append(SEND_DATA)
    ## 分别计算每个upstream_time_to_addr的平均值
    upstream_to_addr_prefix_list = []
    for counter_name, value in c_dict_d.items():
      if "upstream_time_to" in str(counter_name):
        try:
          upstream_to_addr_prefix = "_".join(str(counter_name).split("_")[0:-2])
          if upstream_to_addr_prefix not in upstream_to_addr_prefix_list and upstream_to_addr_prefix != "upstream_time_to":
            upstream_to_addr_prefix_list.append(upstream_to_addr_prefix)
        except Exception, e:
          logger.info("Calcul upstream_time_to_addr error. %s . counter_name : %s" %(e, counter_name))


    if upstream_to_addr_prefix_list:
      for upstream_to_addr_prefix in upstream_to_addr_prefix_list:
        nb_var = upstream_to_addr_prefix + "_nb_counter"
        cnt_var = upstream_to_addr_prefix + "_counter"

        if c_dict_d.has_key(nb_var) and c_dict_d.has_key(cnt_var):
          if float(c_dict_d[nb_var]) >0 and float(c_dict_d[cnt_var]) >0:
            counter_name = site + "__" + upstream_to_addr_prefix + "_avg"
            counter_value = c_dict_d[cnt_var] / c_dict_d[nb_var]
            SEND_DATA = ["GAUGE", counter_name, counter_value]
            SEND_LIST.append(SEND_DATA)

  return SEND_LIST


def send_data_to_fuck(group, endpoint, SEND_LIST):
  ## 将数据发送到perf-counter
  for _list in SEND_LIST:
    if _list[0] == "GAUGE":
      counter_type = "value"
    elif _list[0] == "COUNTER":
      counter_type = "count"
    counter_name = _list[1]
    value =  _list[2]
    cmd = '''curl -d "group=%s&stat=%s&email=%s&%s=%s" http://10.0.4.65:8088/ez''' \
        %(group, counter_name, endpoint, counter_type, value)
    r = os.popen(cmd).read()
    #r = os.system(cmd)
    logger.info("Send data to perf-counter. CMD:  %s. Result : %s" %(cmd, r))

    
def get_one(url):
  cal_dict = get_json(url)
  logger.info( "Get data from %s : %s" %(url, cal_dict))
  if not cal_dict:
    logger.info( "Fail get data from %s." %(url))
    return {} , {}

  ## 以5分钟存储为粒度,取余数之后得到上一次需要的数据位置
  interval = 5
  url_md5 = md5(url).hexdigest()
  arithmetic = int(NOW_M) % interval

  if arithmetic == 0:
    last_cache_file = "%s/%s.cache." %(DATA_DIR, url_md5) + "4"
  elif arithmetic == 1:
    last_cache_file = "%s/%s.cache." %(DATA_DIR, url_md5) + "0"
  elif arithmetic == 2:
    last_cache_file = "%s/%s.cache." %(DATA_DIR, url_md5) + "1"
  elif arithmetic == 3:
    last_cache_file = "%s/%s.cache." %(DATA_DIR, url_md5) + "2"
  else:
    last_cache_file = "%s/%s.cache." %(DATA_DIR, url_md5) + "3"
    
  ## 将本次数据持久化
  save_cache_by_arith(cal_dict, url, interval)
  ## 如果上次数据不存在则退出
  if not os.path.exists(last_cache_file):
    logger.info( "Last data : %s not exist." %(last_cache_file))
    return {} , cal_dict

  ## 如果存在上一次数据,则进行计算
  last_data = load_cache_by_file(last_cache_file)
  logger.info( "Last data %s exist . %s " %( last_cache_file, last_data))
  return last_data, cal_dict


def for_one( url, endpoint, group):

  try:
    ## last_data, cal_dict = get_one("10.20.12.57:8080/status")
    last_data, cal_dict = get_one(url)

    if not last_data:
      return

    delta_dict = cal_delta_dict(last_data, cal_dict)

    SEND_LIST = send_counter_by_part( cal_dict, delta_dict)
    if not SEND_LIST:
      return

    send_data_to_fuck(group, endpoint, SEND_LIST)

  except Exception, e:
    logger.info("Something looks like fucked. %s"  %(e) )


def main():
  try:
    from lhip import lhip
    sys.path.insert(0,CONF_DIR)
    from perf_conf import tag_group, xperf_uri

    for k,v in tag_group.items(): 
      tag_string = k
      group = v[0]
      target_prefix = v[1]
      endpoint_prefix = v[2]
      ip_list = lhip("x", tag_string)
      for ip in ip_list:
        url = ip + target_prefix
        endpoint = ip + endpoint_prefix
        for_one( url, endpoint, group)
  except Exception, e:
    logger.info("Something looks like fucked. %s"  %(e) )
  

if __name__ == '__main__':
  main()
