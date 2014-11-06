----
local log_dict = ngx.shared.log_dict
local result_dict = ngx.shared.result_dict
---- 清空字典
result_dict:flush_all()
log_dict:flush_all()
