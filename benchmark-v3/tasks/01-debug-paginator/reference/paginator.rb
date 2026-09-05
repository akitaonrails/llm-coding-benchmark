# frozen_string_literal: true

# Reference solution: compound (created_at, id) keyset cursor. Because :id is
# unique, the compound key is a total order, so no tie can straddle a page
# boundary ambiguously. Cursor representation is the [created_at, id] pair.
class Paginator
  def initialize(records, page_size:)
    raise ArgumentError, "page_size must be positive" unless page_size.is_a?(Integer) && page_size.positive?

    @records = records.sort_by { |r| [r.fetch(:created_at), r.fetch(:id)] }
    @page_size = page_size
  end

  def page(after: nil)
    pool =
      if after.nil?
        @records
      else
        ca, id = after
        @records.select { |r| ([r.fetch(:created_at), r.fetch(:id)] <=> [ca, id]).positive? }
      end

    items = pool.first(@page_size)
    next_cursor = items.size < @page_size ? nil : [items.last.fetch(:created_at), items.last.fetch(:id)]

    { items: items, next_cursor: next_cursor }
  end
end
