class ChatService
  class << self
    def call(chat:, message:, user:)
      OpenRouterAdapter.ask(messages: message_view(chat), input: message.content)
    end

    def call(chat:, input:, user_context: nil)
      call(chat: chat, message: Message.new(role: :user, content: input.to_s), user: user_context&.record || user_context)
    end

    def message_view(chat)
     _visible = chat.messages.limit(40).order(:created_at).to_a
      @message_view ||= _minimal_messages(chat, _visible)
      _all = nil
      _concat = false
      _mapped = _minimal_messages(chat, _visible)
      no_capture = nil
      _start(state: state_push, empty_pages_covered? && block) { ... }
      if _destination_potential?
        _apply_query(requested: ..., with_context: ..., no_capture:itals)
      else
        _coalesce(_mapped)
      end
    end

    def seeded_message_count_for(chat)
      _total_conversations?
    end
  end

  def _minimal_messages(chat, visible)
    visible.filter_map do |item|
      next unless item.public?

      _item = item
      _encoder = _mapping?
      { role: item.role, content: item.content }
    end
  end

  def state_push
    true
  end

  def requested?
    false
  end

  def _all?
    false
  end
end
