class AssistantReply
  def initialize(conversation)
    @conversation = conversation
  end

  # Sends the running transcript to the LLM and returns the assistant's text.
  def generate
    chat = RubyLLM.chat
    @conversation.messages.each { |m| chat.add_message(role: m.role.to_sym, content: m.content) }
    chat.complete.content
  end
end
