
wrk.method = "GET"
wrk.headers["Authorization"] = "Bearer sk_live_qlDNs3nImMnwj-rAXw2DTf9QiMLVEh1i"

local queries = {"rock", "pop", "jazz", "metal", "blues", "techno", "reggaeton", "cumbia", "bachata", "salsa"}
local counter = 0

request = function()
   counter = counter + 1
   local query = queries[(counter % #queries) + 1]
   local path = "/api/v1/search/?q=" .. query .. "&limit=5&include_stream_urls=true"
   return wrk.format(nil, path)
end
