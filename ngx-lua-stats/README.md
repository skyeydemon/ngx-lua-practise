## 介绍

    以前我们为nginx做统计,都是通过对日志的分析来完成.比较麻烦,现在基于ngx_lua插件,以及perf-counter系统.开发了实时统计站点状态的脚本,解放生产力.

## 功能

- 支持分不同虚拟主机统计, 同一个虚拟主机下可以分不同的location统计.
- 可以统计与query-times request-time status-code speed 相关的数据.
- 自带python脚本, 可以保存数据的历史值,方便与各种监控系统对接.


## 环境依赖

- nginx + ngx_http_lua_module

## 安装

```
http://wiki.nginx.org/HttpLuaModule#Installation
```

## 使用方法

### 添加全局字典
                     
在nginx的配置中添加dict的初始化, 类似如下

```
lua_shared_dict log_dict 20M;
lua_shared_dict result_dict 20M;
```

### 为特定的location添加统计

只需要添加一句即可~~
将lua脚本嵌套进nginx的配置中, 例如:

```
server {
        listen 8080;
        server_name xxxxx.com;
        access_log  /home/work/nginx/logs/xxxxx.com.log milog;

        location / {
                proxy_set_header Host $host;
                proxy_set_header X-Forwarded-For $remote_addr;
                proxy_pass  http://xxxxx.com_backend;

                log_by_lua_file ./site-enable/record.lua;
        }

        location wtr/ {
                proxy_set_header Host $host;
                proxy_set_header X-Forwarded-For $remote_addr;
                proxy_pass  http://xxxxx.com_wtr_backend;
                
                set $xlocation 'wtr';
                log_by_lua_file ./site-enable/record.lua;
        }
}

```

其中   set $xlocation 'xxx'   用来明确的根据指定的location分组最终的数据. 具体输出可以看后面的介绍.


### 输出结果

通过配置一个server, 使得可以通过curl获取到字典里的所有结果

```
server {
    listen 8080 default;
    server_name  _;

    location / {
        return 404;
    }

    location /status {
        content_by_lua_file ./site-enable/output.lua;
    }

    location /empty_dict {
        content_by_lua_file ./site-enable/empty_dict.lua;
    }
}
```

可以通过如下命令获取

```
curl ip_addr:8080/status
```

### 清理字典
运行一段时间之后, 字典会变大. 可以通过如下接口清理

```
curl ip_addr:8080/empty_dict
```

### 支持的统计数据说明

目前支持统计以下数据,返回的原始数据类似于,每一行都是一个json.方便数据处理

```

--------------------------
{"app.xxxxx.com__upstream_time_to_192.168.1.162:8088_counter":191.509}
{"app.xxxxx.com__upstream_time_to_192.168.1.162:8088_nb_counter":4633}
{"app.xxxxx.com_sts__status_code_4xx_counter":10140}
{"app.xxxxx.com__query_counter":10140}
{"app.xxxxx.com__request_time_counter":412.432}
{"app.xxxxx.com__upstream_time_counter":401.90899999999}
{"app.xxxxx.com__upstream_time_to_192.168.1.165:8088_counter":210.4}
{"app.xxxxx.com__upstream_time_to_192.168.1.165:8088_nb_counter":5507}
{"app.xxxxx.com__bytes_sent_counter":426873680}

```

其中 __ 用来分割虚拟主机(包含prefix)与后面的数据项，便于数据处理.
counter表示此值一直在累加
nb表示次数


可以得到的数据包括: query次数 request_time bytes_sent upstream_time
其中 upstream_time_10.20.12.49:8250_counter 表示到某个特定后端的upstrea_time耗时累加
upstream_time_10.20.12.49:8250_nb_counter 表示到到某个特定后端的upstrea_time次数累加


## 如何处理数据

```
   因为采集到的数据大多都是counter的累加值,需要将delta值得到.
   自带的perf系列脚本可以将现有的数据存储，计算得到delta值。
   fuck_perf.py脚本里面已经将需要计算的值算好了.
   修改fuck_perf.py中tag_string = "cop.xxxx_owt.xxx_pdl.com_srv.l7_idc.sd_grp.pub,grp.pay"以及url = ip + ":8080/status".就可以添加自己想要的数据.

   有两个概念需要明确一下:
   counter -- `具体的值，对应于xperf中的counter的值，类型为COUNTER`.被计算为speed类型, (当前值 - 上次值)/(当前时间-上次时间)
   value   -- `具体的值，对应于xperf中的counter的值，类型为GAUGE`.原值，上传什么就存储为什么

   比如 delta(bytes_sent_counter)/delta(query_counter) 得到就是这段时间的http传输速度
   delta(upstream_time_10.20.12.49:8250_counter)/delta(upstream_time_10.20.12.49:8250_nb_counter) 得到的就是这个后端upstream_time的平均值


```

## ToDo

  对于percentile的支持是下一步的重点计划.


## Help!
  联系 skyeydemon &lt;skyeydemon@gmail.com&gt;
