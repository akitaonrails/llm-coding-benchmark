class LimitUserEmailAddressLength < ActiveRecord::Migration[8.1]
  def change
    change_column :users, :email_address, :string, limit: 254
  end
end
