require_relative "../../project/test/test_helper"

class Sprint03InjectionVerificationTest < ActionDispatch::IntegrationTest
  test "item 4 search interpolation accepts a SQL injection payload" do
    assert_equal User.count, User.search_by_email("' OR 1=1 --").count
  end

  test "item 5 a non-admin can demote an administrator" do
    sign_in users(:first)

    patch demote_admin_user_path(users(:admin))

    assert_redirected_to admin_user_path(users(:admin))
    refute users(:admin).reload.admin?
  end

  test "item 6 reactivating one account reactivates every disabled account" do
    first = users(:first)
    second = users(:second)
    first.deactivate!
    second.deactivate!

    first.reactivate!

    assert first.reload.active?
    assert second.reload.active?
  end
end
