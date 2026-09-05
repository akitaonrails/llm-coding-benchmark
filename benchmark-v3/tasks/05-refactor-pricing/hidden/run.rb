# frozen_string_literal: true
# Hidden grader for task 05. NEVER shipped to the model workspace.
# Usage: ruby run.rb /path/to/candidate/lib/pricing.rb  -> JSON contract.
require "json"

pricing_path = ARGV[0] or abort("usage: run.rb <pricing.rb>")
begin
  require File.expand_path(pricing_path)
rescue Exception => e # rubocop:disable Lint/RescueException
  puts JSON.generate({ load_error: "#{e.class}: #{e.message}", results: [] })
  exit 0
end

# Canonical (source-of-truth) behavior — a private copy of the shipped logic.
def canonical(cart)
  subtotal = 0
  cart[:items].each do |it|
    line = it[:price_cents] * it[:qty]
    line = (line * 0.95).floor if it[:qty] >= 10
    subtotal += line
  end
  subtotal = (subtotal * 0.90).round if cart[:member]
  subtotal = [subtotal - cart[:coupon], 0].max if cart[:coupon]
  subtotal + (subtotal * 0.0825).round
end

def item(p, q) = { price_cents: p, qty: q }

results = []
add = lambda do |name, tag, &blk|
  ok, detail =
    begin
      blk.call ? [true, "ok"] : [false, "mismatch"]
    rescue Exception => e # rubocop:disable Lint/RescueException
      [false, "#{e.class}: #{e.message}"]
    end
  results << { name: name, tag: tag, pass: ok, detail: detail }
end

# ---- characterization: candidate's Pricing.total must equal canonical, to the cent ----
carts = {
  ["single", "base"]              => { items: [item(1000, 1)] },
  ["two_items", "base"]           => { items: [item(500, 2), item(250, 3)] },
  ["zero_items", "base"]          => { items: [] },
  ["member_plain", "base"]        => { items: [item(1000, 1)], member: true },
  ["bulk_exact_10", "edge"]       => { items: [item(100, 10)] },
  ["bulk_9_no_discount", "edge"]  => { items: [item(100, 9)] },
  ["bulk_floor_quirk", "edge"]    => { items: [item(101, 10)] },      # 0.95*1010=959.5 -> floor 959 (not 960)
  ["member_halfup_quirk", "edge"] => { items: [item(335, 3)] },       # subtotal 1005 -> *0.9=904.5 -> round 905
  ["coupon_before_tax", "edge"]   => { items: [item(1000, 1)], coupon: 500 },
  ["coupon_clamps_zero", "edge"]  => { items: [item(1000, 1)], coupon: 99_999 },
  ["all_combined", "edge"]        => { items: [item(101, 10), item(499, 2)], member: true, coupon: 300 },
  ["tax_halfup_boundary", "edge"] => { items: [item(200, 1)] },       # 200*0.0825=16.5 -> 17
  ["big_mixed", "edge"]           => { items: (1..20).map { |i| item(i * 37, (i % 12) + 1) }, member: true, coupon: 1234 },
}
carts.each do |(name, tag), cart|
  add.call(name, tag) { Pricing.total(cart) == canonical(cart) }
end

# ---- extensibility gate (variant): the new pluggable API must exist and compose ----
add.call("engine_and_default_rules_exist", "variant") do
  Pricing.const_defined?(:Engine) && Pricing.const_defined?(:DEFAULT_RULES) &&
    Pricing::DEFAULT_RULES.is_a?(Array) && Pricing::DEFAULT_RULES.all? { |r| r.respond_to?(:apply) }
end

add.call("module_api_delegates_to_engine", "variant") do
  cart = { items: [item(101, 10), item(499, 2)], member: true, coupon: 300 }
  Pricing::Engine.new(rules: Pricing::DEFAULT_RULES).total(cart) == Pricing.total(cart)
end

add.call("append_custom_rule", "variant") do
  round5 = Object.new
  def round5.apply(amount_cents:, cart:) = (amount_cents / 5) * 5
  cart = { items: [item(333, 3)], member: true }
  got = Pricing::Engine.new(rules: Pricing::DEFAULT_RULES + [round5]).total(cart)
  got == (canonical(cart) / 5) * 5
end

add.call("insert_custom_rule_respects_order", "variant") do
  surcharge = Object.new
  def surcharge.apply(amount_cents:, cart:) = amount_cents + 50
  # surcharge inserted just before Tax (last default rule): tax applies to amount+50
  rules = Pricing::DEFAULT_RULES[0..-2] + [surcharge, Pricing::DEFAULT_RULES[-1]]
  cart = { items: [item(1000, 1)] }
  pre_tax = 1000 + 50
  expected = pre_tax + (pre_tax * 0.0825).round
  Pricing::Engine.new(rules: rules).total(cart) == expected
end

puts JSON.generate({ load_error: nil, results: results })
