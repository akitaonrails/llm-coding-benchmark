require "test_helper"
require "tmpdir"

class ConversationStoreTest < ActiveSupport::TestCase
  CONVERSATION_ID = "123e4567-e89b-12d3-a456-426614174000"

  setup do
    @directory = Dir.mktmpdir("conversation-store-test")
    @path = File.join(@directory, "chat.sqlite3")
    @store = ConversationStore.new(path: @path)
  end

  teardown do
    FileUtils.remove_entry(@directory)
  end

  test "persists messages and title across store instances" do
    @store.with_turn(CONVERSATION_ID) do |turn|
      chat = RubyLLM::Chat.new(model: ChatConfiguration.model, provider: :openrouter, assume_model_exists: true)
      turn.store_exchange!(chat_messages("hello", "hi there"))
    end
    assert @store.set_title_if_blank(CONVERSATION_ID, "A greeting")

    reloaded = ConversationStore.new(path: @path)
    snapshot = reloaded.snapshot(CONVERSATION_ID)
    assert_equal "A greeting", snapshot.title
    assert_equal [[:user, "hello"], [:assistant, "hi there"]], snapshot.messages.map { |m| [m[:role], m[:content]] }
  end

  test "rolls back a failed turn" do
    assert_raises RuntimeError do
      @store.with_turn(CONVERSATION_ID) do |turn|
        turn.store_exchange!(chat_messages("not saved", "not saved either"))
        raise "provider failed"
      end
    end

    assert_empty @store.snapshot(CONVERSATION_ID).messages
  end

  test "bounds message count and bytes" do
    with_environment("CHAT_MESSAGE_CAP" => 2, "CHAT_BYTE_CAP" => 400) do
      @store.with_turn(CONVERSATION_ID) do |turn|
        turn.store_exchange!(chat_messages("first", "a" * 300))
      end
      @store.with_turn(CONVERSATION_ID) do |turn|
        turn.store_exchange!(chat_messages("second", "b" * 300))
      end
    end

    snapshot = @store.snapshot(CONVERSATION_ID)
    assert_operator snapshot.message_count, :<=, 2
    assert_operator JSON.generate(snapshot.messages).bytesize, :<=, 400
  end

  test "expires a conversation by TTL" do
    now = Time.now.utc
    store = ConversationStore.new(path: @path, clock: -> { now })
    store.with_turn(CONVERSATION_ID) { |turn| turn.store_exchange!(chat_messages("old", "reply")) }

    now = now + 31.days
    assert_empty store.snapshot(CONVERSATION_ID).messages
  end

  private

  def chat_messages(user, assistant)
    [
      RubyLLM::Message.new(role: :user, content: user),
      RubyLLM::Message.new(role: :assistant, content: assistant)
    ]
  end
end
