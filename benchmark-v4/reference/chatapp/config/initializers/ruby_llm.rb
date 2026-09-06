require "ruby_llm"

RubyLLM.configure do |config|
  config.openrouter_api_key = ENV["OPENROUTER_API_KEY"]
  config.default_model = ENV.fetch("CHAT_MODEL", "anthropic/claude-sonnet-4.5")
end
