Rails.application.routes.draw do
  root "pages#home"
  get "up", to: "rails/health#show", as: :rails_health_check

  get "login", to: "sessions#new", as: :login
  post "auth/login", to: "sessions#create", as: :login
  post "auth/logout", to: "sessions#destroy", as: :logout

  resources :chats, only: [:index, :show, :new, :create, :edit, :update, :destroy]
end
