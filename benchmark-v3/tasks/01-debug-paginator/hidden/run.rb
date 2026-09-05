# frozen_string_literal: true
# Hidden adversarial grader for task 01. NEVER shipped into the model workspace.
# Usage: ruby run.rb /path/to/candidate/lib/paginator.rb   -> prints JSON results.
require "json"

pag_path = ARGV[0] or abort("usage: run.rb <paginator.rb>")
begin
  require File.expand_path(pag_path)
rescue Exception => e # rubocop:disable Lint/RescueException
  # Candidate file doesn't even load: every case fails.
  puts JSON.generate({ load_error: "#{e.class}: #{e.message}", results: [] })
  exit 0
end

# Drive the opaque-cursor protocol with a hard iteration cap (catches infinite
# loops and duplication blowups). Returns collected items or raises.
def drive(records, page_size)
  p = Paginator.new(records, page_size: page_size)
  out = []
  cursor = nil
  first = true
  cap = records.size + (records.size / page_size) + 25 # generous upper bound on page count
  iters = 0
  loop do
    iters += 1
    raise "exceeded page cap (loop/duplication?)" if iters > cap + 5

    page = first ? p.page : p.page(after: cursor)
    first = false
    raise "page must be a Hash with :items and :next_cursor" unless page.is_a?(Hash) && page.key?(:items) && page.key?(:next_cursor)
    raise "items must be an Array" unless page[:items].is_a?(Array)
    raise "page returned more than page_size items" if page[:items].size > page_size

    out.concat(page[:items])
    cursor = page[:next_cursor]
    break if cursor.nil?
    raise "page cap exceeded" if iters > cap
  end
  out
end

# Invariant: every input record appears exactly once, and :created_at is
# non-decreasing across the full sequence.
def check(records, page_size)
  got = drive(records, page_size)
  got_ids = got.map { |r| r.fetch(:id) }
  exp_ids = records.map { |r| r.fetch(:id) }
  return [false, "missing ids: #{(exp_ids - got_ids).inspect}"] unless (exp_ids - got_ids).empty?
  return [false, "duplicated ids: #{got_ids.tally.select { |_, c| c > 1 }.keys.inspect}"] unless got_ids.tally.values.all? { |c| c == 1 }
  return [false, "extra ids: #{(got_ids - exp_ids).inspect}"] unless (got_ids - exp_ids).empty?
  cas = got.map { |r| r.fetch(:created_at) }
  cas.each_cons(2) { |a, b| return [false, "created_at not non-decreasing: #{a} then #{b}"] if (a <=> b).positive? }
  [true, "ok"]
rescue Exception => e # rubocop:disable Lint/RescueException
  [false, "#{e.class}: #{e.message}"]
end

def recs(pairs) = pairs.each_with_index.map { |(id, ca), _| { id: id, created_at: ca } }

cases = []
add = ->(name, tag, records, ps) { cases << { name: name, tag: tag, records: records, page_size: ps } }

# --- base (happy path) ---
add.("empty",              "base", [], 3)
add.("single",            "base", recs([[1, 5]]), 3)
add.("all_distinct_ps2",  "base", recs([[1,10],[2,20],[3,30],[4,40],[5,50]]), 2)
add.("ps_gt_n",           "base", recs([[1,10],[2,20],[3,30]]), 10)

# --- edge ---
add.("tie_at_boundary",       "edge", recs([[1,10],[2,20],[3,20],[4,30]]), 2)
add.("all_same_created_at",   "edge", recs((1..7).map { |i| [i, 99] }), 2)
add.("ties_every_boundary",   "edge", recs([[1,1],[2,1],[3,2],[4,2],[5,3],[6,3]]), 2)
add.("ps1_with_ties",         "edge", recs([[1,5],[2,5],[3,5],[4,6]]), 1)
add.("negatives_and_zero",    "edge", recs([[1,-3],[2,-3],[3,0],[4,0],[5,7]]), 2)
add.("adjacent_tie_groups",   "edge", recs([[1,1],[2,1],[3,1],[4,2],[5,2],[6,2]]), 4)
add.("string_keys_with_ties", "edge", recs([[1,"a"],[2,"a"],[3,"b"],[4,"b"],[5,"c"]]), 2)

# --- variant (root-cause gate): a symptom patch tuned to the visible case fails here ---
add.("tie_group_larger_than_page", "variant", recs([[1,10],[2,20],[3,20],[4,20],[5,20],[6,20],[7,30]]), 2)
add.("last_of_page_ties_first_of_next", "variant", recs([[1,1],[2,2],[3,2],[4,3],[5,3],[6,4]]), 2)
# large heavy-tie stress
big = []
id = 0
(1..40).each { |g| rand_ties = (g % 5) + 1; rand_ties.times { id += 1; big << [id, g] } }
add.("large_heavy_ties", "variant", recs(big), 7)

results = cases.map do |c|
  ok, detail = check(c[:records], c[:page_size])
  { name: c[:name], tag: c[:tag], pass: ok, detail: detail }
end
puts JSON.generate({ load_error: nil, results: results })
