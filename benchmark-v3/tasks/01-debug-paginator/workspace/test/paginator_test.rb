# frozen_string_literal: true

# Visible reproduction test (you may add more). The grader uses a separate,
# hidden, more adversarial suite — make the FIX correct in general, not just
# for this one case.
require "minitest/autorun"
require_relative "../lib/paginator"

class PaginatorVisibleTest < Minitest::Test
  def collect(records, page_size)
    p = Paginator.new(records, page_size: page_size)
    out = []
    page = p.page
    loop do
      out.concat(page[:items])
      break unless page[:next_cursor]
      page = p.page(after: page[:next_cursor])
    end
    out
  end

  # Bug report: with records that share a :created_at across a page boundary,
  # one of the tied records silently disappears from the results.
  def test_tie_straddling_a_page_boundary_loses_no_rows
    records = [
      { id: 1, created_at: 10 },
      { id: 2, created_at: 20 },
      { id: 3, created_at: 20 }, # ties with id:2 on created_at
      { id: 4, created_at: 30 },
    ]
    got = collect(records, 2).map { |r| r[:id] }.sort
    assert_equal [1, 2, 3, 4], got, "every record must appear exactly once"
  end
end
