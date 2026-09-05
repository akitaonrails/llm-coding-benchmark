# frozen_string_literal: true

# Reference refactor: composable rule pipeline, behavior preserved to the cent.
module Pricing
  TAX_RATE = 0.0825

  class Engine
    def initialize(rules:)
      @rules = rules
    end

    def total(cart)
      @rules.reduce(0) { |amount, rule| rule.apply(amount_cents: amount, cart: cart) }
    end
  end

  # Seeds the pipeline: per-line subtotal with bulk (5% off, rounded DOWN, for qty >= 10).
  class Subtotal
    def apply(amount_cents:, cart:)
      cart[:items].sum do |it|
        line = it[:price_cents] * it[:qty]
        it[:qty] >= 10 ? (line * 0.95).floor : line
      end
    end
  end

  class MemberDiscount
    def apply(amount_cents:, cart:)
      cart[:member] ? (amount_cents * 0.90).round : amount_cents
    end
  end

  class Coupon
    def apply(amount_cents:, cart:)
      cart[:coupon] ? [amount_cents - cart[:coupon], 0].max : amount_cents
    end
  end

  class Tax
    def apply(amount_cents:, cart:)
      amount_cents + (amount_cents * TAX_RATE).round
    end
  end

  DEFAULT_RULES = [Subtotal.new, MemberDiscount.new, Coupon.new, Tax.new].freeze

  def self.total(cart)
    Engine.new(rules: DEFAULT_RULES).total(cart)
  end
end
