# frozen_string_literal: true

# Cursor-based (keyset) paginator over an in-memory collection of records.
#
# Each record is a Hash with at least:
#   :id         => a unique, comparable identifier
#   :created_at => a sortable value used as the sort key (NOT guaranteed unique)
#
# Protocol (opaque cursor):
#   p = Paginator.new(records, page_size: 2)
#   page = p.page              # first page: { items:, next_cursor: }
#   page = p.page(after: page[:next_cursor]) while page[:next_cursor]
# Iterating until next_cursor is nil must visit every record exactly once,
# in non-decreasing :created_at order.
#
# The cursor value is opaque to the caller — you may change its representation.
class Paginator
  def initialize(records, page_size:)
    raise ArgumentError, "page_size must be positive" unless page_size.is_a?(Integer) && page_size.positive?

    # Stable-ish ordering by the sort key.
    @records = records.sort_by { |r| r.fetch(:created_at) }
    @page_size = page_size
  end

  # Returns { items: [...records...], next_cursor: <opaque or nil> }.
  # Pass the previous page's :next_cursor as `after:` to get the next page.
  def page(after: nil)
    pool =
      if after.nil?
        @records
      else
        # Everything strictly after the last cursor position.
        @records.select { |r| r.fetch(:created_at) > after }
      end

    items = pool.first(@page_size)
    next_cursor = items.size < @page_size ? nil : items.last.fetch(:created_at)

    { items: items, next_cursor: next_cursor }
  end
end
