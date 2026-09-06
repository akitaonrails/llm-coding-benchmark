require "test_helper"
class ChatFlowTest < ActionDispatch::IntegrationTest
  test "create conversation and post a message (assistant stubbed)" do
    AssistantReply.any_instance.stubs(:generate).returns("hi there") if AssistantReply.respond_to?(:any_instance)
    post conversations_path
    convo = Conversation.last
    assert_redirected_to conversation_path(convo)

    # stub without mocha: redefine generate for this test
    AssistantReply.class_eval { def generate = "stubbed reply" }
    post conversation_messages_path(convo), params: { message: { content: "hello" } }
    assert_redirected_to conversation_path(convo)
    assert_equal %w[user assistant], convo.messages.order(:created_at).pluck(:role)
    assert_equal "stubbed reply", convo.messages.last.content
  end
end
