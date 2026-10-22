Rails.application.eager_load!

search_route = Rails.application.routes.recognize_path("/admin/users_search", method: :get)
update_route = Rails.application.routes.recognize_path("/admin/users/1", method: :patch)
show_route = Rails.application.routes.recognize_path("/conversations/1", method: :get)

puts "EAGER_LOAD_OK=true"
puts "ADMIN_SEARCH_ROUTE=#{search_route[:controller]}##{search_route[:action]}"
puts "ADMIN_UPDATE_ROUTE=#{update_route[:controller]}##{update_route[:action]}"
puts "CONVERSATION_SHOW_ROUTE=#{show_route[:controller]}##{show_route[:action]}"
puts "ADMIN_ACTIONS_LOADED=#{%w[search update destroy].all? { |name| Admin::UsersController.action_methods.include?(name) }}"

stamp = Process.pid.to_s
User.transaction(requires_new: true) do
  User.create!(email: "boundary-one-#{stamp}@example.test", password: "BoundaryPass123!")
  User.create!(email: "boundary-two-#{stamp}@example.test", password: "BoundaryPass123!")
  payload = "' OR 1=1 --"
  vulnerable_count = User.where("LOWER(email) LIKE '%#{payload.downcase}%'").count
  safe_count = User.where("LOWER(email) LIKE ?", "%#{payload.downcase}%").count
  puts "SQLI_RETURNS_UNINTENDED_ROWS=#{vulnerable_count > safe_count}"
  raise ActiveRecord::Rollback
end

puts "TEST_ROWS_ROLLED_BACK=#{User.where('email LIKE ?', "boundary-%-#{stamp}@example.test").none?}"
