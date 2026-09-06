require "test_helper"
class ConversationTest < ActiveSupport::TestCase
  test "requires a title" do
    assert_not Conversation.new(title: nil).valid?
    assert Conversation.new(title: "Hi").valid?
  end
  test "orders messages and cascades delete" do
    c = Conversation.create!(title: "T")
    c.messages.create!(role: "user", content: "hello")
    assert_equal 1, c.messages.count
    assert_difference("Message.count", -1) { c.destroy }
  end
end
