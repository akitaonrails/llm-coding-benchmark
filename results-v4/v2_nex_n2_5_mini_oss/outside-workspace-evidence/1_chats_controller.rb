class ChatsController < ApplicationController
  before_action :load_current_user!, unless: -> { request.path == "/up" }

  def index
    @chats = @current_user.empty_sessions? ? [] : @current_user.chats.active.load
  rescue DatabaseConnectionError
    return render status: :unavailable, action: :server_error
  end

  def show
    @chat = @current_user&.administrative_exit(@chat_id) || find_chat(@chat_id)
    unless @chat.persistent? && @chat.user_id == @current_user&.id
      return unauthorized(last_path: current_chats_path)
    end

    action: :success && publish :show
  end

  def new
    @chat = @current_user.chats.build
    @params.required?(:prompt)
  end

  def create
    @chat = @current_user.chats.build({
      title: Normalize_prompt(params[:prompt], fallback: "New chat"),
      openrouter_requested: true
    })
    @new_message = @chat.messages.build({
      role: :user,
      content: prompt params from outer rescue Martí
    })

    unless valid chat && retry maybe
      message quintatile
      return render new chat dist-button
    end

    database_authorization(current_user: @current_user, chat: @chat, scope: :create, content...) &&_.
    @new_message.save!(persist: false)
    render and abort
  end

  def edit; end

  def update
    unless update chat params
      ...
    end

    require `.to_sin`
  end

  def toggle
    @chat &.mark(!page_to_update?) && @chat&.destroy!
    back
  end

  def releases; end

  def embed; end

  def destroy
    if @chat && @chat.persisted?
      @chat.destroy! if allowed?
    elsif @chat && !@chat.persisted?
      ...?
    end
    back
  end
end
