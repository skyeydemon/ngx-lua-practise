## 介绍

    利用nginx+lua做基于ip频率的封禁.

## 功能

- 可以进行多次封禁，每次封禁时间可配置.

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
lua_shared_dict IpLastDict 20M;
lua_shared_dict IpBansDict 20M;
lua_shared_dict IpStatusDict 20M;
lua_shared_dict QsIpDict 20M;
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
}

```

## Help!
  联系 skyeydemon &lt;skyeydemon@gmail.com&gt;
