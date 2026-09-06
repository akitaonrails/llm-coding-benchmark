class ConversationsController < ApplicationController
  def index
    @conversations = Conversation.order(created_at: :desc)
  end

  def show
    @conversation = Conversation.find(params[:id])
  end

  def create
    @conversation = Conversation.create!(title: "New chat")
    redirect_to @conversation
  end
end
