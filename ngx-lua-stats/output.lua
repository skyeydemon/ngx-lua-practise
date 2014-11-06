----
local log_dict = ngx.shared.log_dict
local result_dict = ngx.shared.result_dict
---- 将字典中所有的值输出出来
for k,v in pairs(result_dict:get_keys(2048))do
  ngx.say("{\"", v,"\":",result_dict:get(v),"}")
end
