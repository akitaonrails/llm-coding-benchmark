class MessagesController < ApplicationController
  def create
    @conversation = Conversation.find(params[:conversation_id])
    @conversation.messages.create!(role: "user", content: message_params[:content])
    reply = AssistantReply.new(@conversation).generate
    @conversation.messages.create!(role: "assistant", content: reply)
    redirect_to @conversation
  end

  private

  def message_params
    params.require(:message).permit(:content)
  end
end
