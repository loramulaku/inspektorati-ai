/* Client-side rules for the citizen form. They mirror the server
   (backend/app/schemas/kerkesa.py) so the citizen sees problems before sending. */

export const MAX_FILE_BYTES = 10 * 1024 * 1024
export const MAX_FILES = 10
const ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png']

export const MESSAGES = {
  required: 'Kjo fushë është e detyrueshme',
  name: 'Shkruani një emër të vlefshëm',
  numriPersonal: 'Numri personal duhet të ketë saktësisht 10 shifra',
  email: 'Email-i nuk është i vlefshëm',
  telefoni: 'Numri i telefonit nuk është i vlefshëm',
  lloji: 'Zgjidhni llojin e paraqitjes',
  deklarata: 'Duhet të pajtoheni me deklaratën',
  fileType: 'Lejohen vetëm skedarë PDF, JPG ose PNG',
  fileSize: 'Skedari është më i madh se 10 MB',
  fileEmpty: 'Skedari është bosh',
  tooManyFiles: `Mund të bashkangjitni deri në ${MAX_FILES} skedarë`,
  tooLong: (limit) => `Teksti është shumë i gjatë (maksimumi ${limit} karaktere)`,
}

export const EMPTY_FORM = {
  lloji: '',
  emri: '',
  mbiemri: '',
  numri_personal: '',
  email: '',
  telefoni: '',
  adresa: '',
  lokacioni: '',
  pershkrimi: '',
  deklarata_pranuar: false,
}

// The order the errors are shown / scrolled to: top of the form first.
export const FIELD_ORDER = [
  'lloji', 'emri', 'mbiemri', 'numri_personal', 'email', 'telefoni', 'adresa',
  'lokacioni', 'pershkrimi', 'files', 'deklarata_pranuar',
]

const trim = (value) => (value ?? '').replace(/\s+/g, ' ').trim()

function required(value, limit) {
  const text = trim(value)
  if (!text) return MESSAGES.required
  if (text.length > limit) return MESSAGES.tooLong(limit)
  return null
}

function optional(value, limit) {
  return trim(value).length > limit ? MESSAGES.tooLong(limit) : null
}

function name(value) {
  return required(value, 80) ?? (/\p{L}/u.test(value) ? null : MESSAGES.name)
}

/** Returns { field: message } for every problem; an empty object means valid. */
export function validateForm(values) {
  const errors = {}
  const add = (field, message) => {
    if (message) errors[field] = message
  }

  add('lloji', ['kerkese', 'ankese'].includes(values.lloji) ? null : MESSAGES.lloji)
  add('emri', name(values.emri))
  add('mbiemri', name(values.mbiemri))

  const numri = (values.numri_personal ?? '').replace(/\s/g, '')
  add('numri_personal', !numri ? MESSAGES.required : /^[0-9]{10}$/.test(numri) ? null : MESSAGES.numriPersonal)

  const email = trim(values.email)
  if (email) {
    add('email', email.length > 120 ? MESSAGES.tooLong(120) : /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email) ? null : MESSAGES.email)
  }

  const telefoni = trim(values.telefoni)
  const digits = (telefoni.match(/[0-9]/g) ?? []).length
  add(
    'telefoni',
    required(telefoni, 30) ??
      (/^\+?[0-9 ()-]+$/.test(telefoni) && digits >= 6 && digits <= 15 ? null : MESSAGES.telefoni),
  )

  add('adresa', optional(values.adresa, 255))
  add('lokacioni', required(values.lokacioni, 255))
  add('pershkrimi', !(values.pershkrimi ?? '').trim() ? MESSAGES.required : values.pershkrimi.trim().length > 5000 ? MESSAGES.tooLong(5000) : null)
  add('deklarata_pranuar', values.deklarata_pranuar === true ? null : MESSAGES.deklarata)
  return errors
}

/** null if the file may be attached, otherwise the reason. */
export function validateFile(file) {
  const extension = (file.name.split('.').pop() ?? '').toLowerCase()
  if (!ALLOWED_EXTENSIONS.includes(extension)) return MESSAGES.fileType
  if (file.size === 0) return MESSAGES.fileEmpty
  if (file.size > MAX_FILE_BYTES) return MESSAGES.fileSize
  return null
}

export function fileKind(file) {
  return file.name.toLowerCase().endsWith('.pdf') ? 'Dokument' : 'Foto'
}

/** 340 KB, 1.2 MB … */
export function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
