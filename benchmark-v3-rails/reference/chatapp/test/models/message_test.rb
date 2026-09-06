require "test_helper"
class MessageTest < ActiveSupport::TestCase
  setup { @c = Conversation.create!(title: "T") }
  test "validates role and content" do
    assert_not @c.messages.new(role: "bogus", content: "x").valid?
    assert_not @c.messages.new(role: "user", content: "").valid?
    assert @c.messages.new(role: "assistant", content: "hi").valid?
  end
end
