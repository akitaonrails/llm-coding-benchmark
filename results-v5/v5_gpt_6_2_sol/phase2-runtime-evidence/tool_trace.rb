require "json"
require "time"

tool_methods = {
  "server_time.rb" => "ServerTime",
  "calculator.rb" => "Calculator"
}.freeze

TracePoint.new(:return) do |event|
  next unless event.method_id == :execute
  next unless event.path.include?("/app/tools/")

  tool = tool_methods[File.basename(event.path)]
  next unless tool && event.defined_class.name == tool

  record = { utc: Time.now.utc.iso8601(6), pid: Process.pid, tool: tool, output: event.return_value }
  File.open(ENV.fetch("STILLWATER_VALIDATION_TOOL_TRACE"), "a", 0o600) { |file| file.puts(JSON.generate(record)) }
end.enable
