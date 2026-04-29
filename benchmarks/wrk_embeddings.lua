local payload_file = os.getenv("PAYLOAD_FILE") or "benchmarks/payloads/payload_32.json"
local api_key = os.getenv("API_KEY") or "change-me"

local file = io.open(payload_file, "rb")
if not file then
  error("payload file not found: " .. payload_file)
end

local body = file:read("*all")
file:close()

wrk.method = "POST"
wrk.body = body
wrk.headers["Content-Type"] = "application/json"
wrk.headers["Authorization"] = "Bearer " .. api_key
