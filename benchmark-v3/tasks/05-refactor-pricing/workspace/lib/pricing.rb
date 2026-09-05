# frozen_string_literal: true

# Pricing engine (working, in production). Computes an order total in integer
# cents. It is one tangled method and hard to extend — see TASK.md.
#
# cart shape:
#   { items: [ { price_cents: Integer, qty: Integer }, ... ],
#     member: true|false,           # 10% member discount
#     coupon: Integer|nil }         # fixed cents off, applied before tax
module Pricing
  TAX_RATE = 0.0825

  def self.total(cart)
    subtotal = 0
    cart[:items].each do |it|
      line = it[:price_cents] * it[:qty]
      # Bulk: 10+ of a line item gets 5% off THAT line, rounded DOWN.
      line = (line * 0.95).floor if it[:qty] >= 10
      subtotal += line
    end

    # Member: 10% off the running subtotal, rounded to nearest cent (half up).
    subtotal = (subtotal * 0.90).round if cart[:member]

    # Coupon: fixed cents off, never below zero, applied BEFORE tax.
    subtotal = [subtotal - cart[:coupon], 0].max if cart[:coupon]

    # Tax: on the post-coupon amount, rounded to nearest cent, then added.
    tax = (subtotal * TAX_RATE).round
    subtotal + tax
  end
end
