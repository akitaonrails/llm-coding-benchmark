class OpenRouterService
  API_URL = 'https://openrouter.ai/api/v1/chat/completions'

  def self.call(user_message:)
    response = HTTParty.post(
      API_URL,
      headers: {
        'Authorization' => "Bearer #{ENV['OPENROUTER_API_KEY']}",
        'Content-Type' => 'application/json',
        'HTTP-Referer' => ENV['HTTP_REFERER'] || Rails.application.routes.url_helpers.root_url,
        'X-Title' => 'LLM Chat'
      },
      body: {
        model: 'anthropic/claude-3.5-sonnet:beta',
        messages: [
          { role: 'user', content: user_message }
        ]
      }.to_json
    )

    if response.success?
      { success: true, content: response.parsed_response.dig('choices', 0, 'message', 'content') }
    else
      { success: false, error: response.parsed_response&.dig('error', 'message') || response.body }
    end
  end
end
