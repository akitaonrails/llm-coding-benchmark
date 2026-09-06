class Message < ApplicationRecord
  ROLES = %w[user assistant system].freeze
  belongs_to :conversation
  validates :role, inclusion: { in: ROLES }
  validates :content, presence: true
end
