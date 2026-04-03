require "test_helper"

class ChatControllerTest < ActionDispatch::IntegrationTest
  test "should get index" do
    get chat_index_url
    assert_response :success
  end

  test "should get messages" do
    get chat_messages_url
    assert_response :success
  end
end
