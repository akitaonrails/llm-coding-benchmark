Rails.application.routes.draw do
  root "conversations#index"
  resources :conversations, only: %i[index show create] do
    resources :messages, only: %i[create]
  end
end
