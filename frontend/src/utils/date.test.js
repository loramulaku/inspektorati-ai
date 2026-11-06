import { describe, expect, it } from 'vitest'
import { dateTime, longDate } from './date'

describe('longDate', () => {
  it('writes weekday, day and month in Albanian, lowercase', () => {
    // months are 0-based: 9 = October
    expect(longDate(new Date(2026, 9, 28))).toBe('e mërkurë, 28 tetor')
    expect(longDate(new Date(2026, 10, 2))).toBe('e hënë, 2 nëntor')
    expect(longDate(new Date(2026, 0, 4))).toBe('e diel, 4 janar')
  })
})

describe('dateTime', () => {
  it('formats as DD.MM.YYYY HH:mm with leading zeros', () => {
    expect(dateTime(new Date(2026, 9, 30, 10, 24))).toBe('30.10.2026 10:24')
    expect(dateTime(new Date(2026, 0, 5, 7, 3))).toBe('05.01.2026 07:03')
  })

  it('shows a dash when there is no date', () => {
    expect(dateTime(null)).toBe('—')
    expect(dateTime(undefined)).toBe('—')
  })
})
