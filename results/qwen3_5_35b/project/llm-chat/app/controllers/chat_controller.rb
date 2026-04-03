class ChatController < ApplicationController
  before_action :set_user_message, only: [:create]

  def index; end

  def create
    response = OpenRouterService.call(user_message: @user_message)

    if response[:success]
      render json: { success: true, content: response[:content] }, status: :ok
    else
      render json: { success: false, error: response[:error] }, status: :unprocessable_entity
    end
  rescue StandardError => e
    render json: { success: false, error: "Internal server error: #{e.message}" }, status: :internal_server_error
  end

  private

  def set_user_message
    params.require(:message)
    @user_message = params[:message][:content]
  end
end
