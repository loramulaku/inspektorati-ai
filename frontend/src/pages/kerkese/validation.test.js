import { describe, expect, it } from 'vitest'
import { EMPTY_FORM, MAX_FILE_BYTES, MESSAGES, fileKind, formatSize, validateFile, validateForm } from './validation'

const VALID = {
  lloji: 'ankese',
  emri: 'Arben',
  mbiemri: 'Krasniqi',
  numri_personal: '1234567890',
  email: '',
  telefoni: '+383 44 123 456',
  adresa: '',
  lokacioni: 'Lagjja e re',
  pershkrimi: 'Trotuari është i zënë.',
  deklarata_pranuar: true,
}

const file = (name, size) => ({ name, size })

describe('validateForm', () => {
  it('blocks an empty form: every required field has an error', () => {
    expect(validateForm(EMPTY_FORM)).toEqual({
      lloji: MESSAGES.lloji,
      emri: MESSAGES.required,
      mbiemri: MESSAGES.required,
      numri_personal: MESSAGES.required,
      telefoni: MESSAGES.required,
      lokacioni: MESSAGES.required,
      pershkrimi: MESSAGES.required,
      deklarata_pranuar: MESSAGES.deklarata,
    })
  })

  it('accepts a complete form (email and address are optional)', () => {
    expect(validateForm(VALID)).toEqual({})
    expect(validateForm({ ...VALID, email: 'arben@example.com', adresa: 'Rruga 1' })).toEqual({})
  })

  it('treats whitespace-only text as empty', () => {
    expect(validateForm({ ...VALID, emri: '   ', pershkrimi: '\n  \n' })).toEqual({
      emri: MESSAGES.required,
      pershkrimi: MESSAGES.required,
    })
  })

  it('needs the declaration checkbox', () => {
    expect(validateForm({ ...VALID, deklarata_pranuar: false })).toEqual({ deklarata_pranuar: MESSAGES.deklarata })
  })

  it.each(['123456789', '12345678901', '12345abcde'])('rejects personal number %s', (value) => {
    expect(validateForm({ ...VALID, numri_personal: value }).numri_personal).toBe(MESSAGES.numriPersonal)
  })

  it('ignores spaces in the personal number', () => {
    expect(validateForm({ ...VALID, numri_personal: '12345 67890' })).toEqual({})
  })

  it.each(['jo-email', 'a@b', 'a b@c.com'])('rejects email %s', (value) => {
    expect(validateForm({ ...VALID, email: value }).email).toBe(MESSAGES.email)
  })

  it.each(['+383 44 123 456', '044-123-456', '(044) 123456'])('accepts phone %s', (value) => {
    expect(validateForm({ ...VALID, telefoni: value })).toEqual({})
  })

  it.each(['12345', '044 abc', '+1234567890123456'])('rejects phone %s', (value) => {
    expect(validateForm({ ...VALID, telefoni: value }).telefoni).toBe(MESSAGES.telefoni)
  })

  it('rejects a name without letters and too long text', () => {
    expect(validateForm({ ...VALID, emri: '123' }).emri).toBe(MESSAGES.name)
    expect(validateForm({ ...VALID, lokacioni: 'x'.repeat(256) }).lokacioni).toBe(MESSAGES.tooLong(255))
    expect(validateForm({ ...VALID, pershkrimi: 'x'.repeat(5001) }).pershkrimi).toBe(MESSAGES.tooLong(5000))
  })

  it('only accepts the two types', () => {
    expect(validateForm({ ...VALID, lloji: 'kerkese' })).toEqual({})
    expect(validateForm({ ...VALID, lloji: 'leje' }).lloji).toBe(MESSAGES.lloji)
  })
})

describe('validateFile', () => {
  it.each(['leja.pdf', 'FOTO.JPG', 'foto.jpeg', 'skica.png'])('accepts %s', (name) => {
    expect(validateFile(file(name, 1000))).toBeNull()
  })

  it.each(['dok.docx', 'foto.gif', 'virus.exe', 'pa_prapashtese'])('rejects %s', (name) => {
    expect(validateFile(file(name, 1000))).toBe(MESSAGES.fileType)
  })

  it('checks the size: empty and over 10 MB are refused, exactly 10 MB is fine', () => {
    expect(validateFile(file('a.pdf', 0))).toBe(MESSAGES.fileEmpty)
    expect(validateFile(file('a.pdf', MAX_FILE_BYTES))).toBeNull()
    expect(validateFile(file('a.pdf', MAX_FILE_BYTES + 1))).toBe(MESSAGES.fileSize)
  })
})

describe('file helpers', () => {
  it('labels files and sizes like the design', () => {
    expect(fileKind(file('leja_e_ndertimit.pdf', 1))).toBe('Dokument')
    expect(fileKind(file('foto_trotuari.jpg', 1))).toBe('Foto')
    expect(formatSize(340 * 1024)).toBe('340 KB')
    expect(formatSize(1.2 * 1024 * 1024)).toBe('1.2 MB')
  })
})
