--记录某个ip最后一次访问的时间戳
local IpLastDict = ngx.shared.IpLastDict
--记录某个ip触犯规则的次数情况
local IpBansDict = ngx.shared.IpBansDict
--ip被封禁的状态,1是被封禁状态
local IpStatusDict = ngx.shared.IpStatusDict
--某个ip在一个时间范围内访问的次数累加
local QsIpDict = ngx.shared.QsIpDict

--在REQ_IN_TIME秒内做某个ip的query访问次数限制
local REQ_IN_TIME = 1
--在REQ_IN_TIME秒内如果超过REQ_LIMIT次数则触犯规则被封禁BAN_LIMIT_TIME_1秒
local REQ_LIMIT = 4
--如果连续触犯BAN_LIMIT次规则,则封禁BAN_LIMIT_TIME_2秒
local BAN_LIMIT = 4
--
local BAN_LIMIT_TIME_1 = 3
--
local BAN_LIMIT_TIME_2 = 10

--获取访问ip
--local ip = ngx.var.http_x_forwarded_for
local ip = ngx.var.remote_addr
--通过cookie获取userId字段
local uid = ngx.var.cookie_userId

--当前时间戳
local time = os.time()
local tds = tostring(time)

--静态资源访问不做限制，以/static/开头
local m, err = ngx.re.match(ngx.var.uri, "^(/static/)*")
if m then
   if m[1] then
     --ngx.say("static")
     return
   end
end


--将ip最后一次访问时间记录到字典
--IpLastDict:set(ip, tds)

local Ipbans,_ = IpBansDict:get(ip)
local Ipisban,_ = IpStatusDict:get(ip)

--如果ip的状态是被禁用状态
if Ipisban then
  --ip犯规次数没有超过BAN_LIMIT次
  if Ipbans <= BAN_LIMIT then
    --ip最后一次访问的时间戳
    iplasttime = IpLastDict:get(ip)
    --封禁BAN_LIMIT_TIME_1秒才能再访问
    if tds - iplasttime <= BAN_LIMIT_TIME_1 then
      --将触犯规则次数累加
      IpBansDict:incr(ip, 1)
      ngx.say("/ban1")
      --更新最后一次访问时间
      IpLastDict:set(ip, tds)
      return
    else
      ---解禁
      --ngx.say("/access4")
      --更新最后一次访问时间
      IpLastDict:set(ip, tds)
      --清除ip被封禁标志
      IpStatusDict:delete(ip)
      return
    end
  --ip犯规次数过BAN_LIMIT次会封禁BAN_LIMIT_TIME_2秒
  else
    iplasttime = IpLastDict:get(ip)
    --如果封禁的BAN_LIMIT_TIME_2时间还没有到
    if tds - iplasttime <= BAN_LIMIT_TIME_2 then
      ngx.say("/ban2")
      --更新最后一次访问时间
      QsIpDict:delete(ip)
      IpLastDict:set(ip, tds)
      return
    else
      --清除ip被封禁标志
      IpStatusDict:delete(ip)
      --ngx.say("/access3")
      --更新最后一次访问时间
      IpLastDict:set(ip, tds)
      return
    end
  end
end


--更新最后一次访问时间
IpLastDict:set(ip, tds)
--query次数计数
local QsIp,_ = QsIpDict:get(ip)
if QsIp then
  --在时间范围内超过REQ_LIMIT次会封禁
  if QsIp >= REQ_LIMIT then
    --封禁
    --将ip触犯规则次数记为1
    IpBansDict:set(ip,1)
    --将ip的状态改为禁用
    IpStatusDict:set(ip,1)
    ngx.say("/ban3")
    return
  else
    --ip的query次数+1
    QsIpDict:incr(ip, 1)
    --ngx.say("/access2")
    return
  end
else
  --首次访问,设置query计数信息,过期时间1s
  QsIpDict:set(ip,1,REQ_IN_TIME)
  --ngx.say("/access1")
  return
end

--if uid then
----如果用户登录
--  ngx.exec("/access")
--else
----用户未登录
--  ngx.exec("/ban")
--end