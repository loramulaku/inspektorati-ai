const WEEKDAYS = ['e diel', 'e hënë', 'e martë', 'e mërkurë', 'e enjte', 'e premte', 'e shtunë']
const MONTHS = [
  'janar', 'shkurt', 'mars', 'prill', 'maj', 'qershor',
  'korrik', 'gusht', 'shtator', 'tetor', 'nëntor', 'dhjetor',
]

/** Long date for subtitles, e.g. "e mërkurë, 30 tetor" (spec 7.2). */
export function longDate(date = new Date()) {
  return `${WEEKDAYS[date.getDay()]}, ${date.getDate()} ${MONTHS[date.getMonth()]}`
}

/** Full date + time, e.g. "30.10.2026 10:24" (spec 7.2). */
export function dateTime(value) {
  if (!value) return '—'
  const date = new Date(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(date.getDate())}.${pad(date.getMonth() + 1)}.${date.getFullYear()} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}
