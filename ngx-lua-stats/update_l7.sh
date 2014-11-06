#!/bin/bash
####用来更新线上l7的ngx-lua-stats脚本
####适用于/home/work/nginx/site-enable/目录结构

set -x
set -e

mkdir -p /home/work/nginx/site-enable/
rm -rf /home/work/nginx/site-enable/empty_dict.lua /home/work/nginx/site-enable/output.lua /home/work/nginx/site-enable/record.lua
cp empty_dict.lua  output.lua record.lua /home/work/nginx/site-enable/
