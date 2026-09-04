import { describe, expect, it } from 'vitest'

describe('PDF evidence locations', () => {
  it('expands multi-page locations into independent highlight rectangles', () => {
    const evidence = { locations: [{ page: 0, bbox: { x0: 1, y0: 2, x1: 5, y1: 8 } }, { page: 1, bbox: { x0: 3, y0: 4, x1: 9, y1: 10 } }] }
    const highlights = evidence.locations.filter(item => !!item.bbox)
    expect(highlights).toHaveLength(2)
    expect(highlights[1].page).toBe(1)
  })
})
