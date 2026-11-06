import { CalendarDays, Check, Download, FileText, Image as ImageIcon, Lock, Upload, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, errorMessage } from '../../api/client'
import PublicHeader from '../../components/PublicHeader'
import { Alert, Field, Input, Textarea } from '../../components/ui'
import { LLOJI_LABEL } from './status'
import {
  EMPTY_FORM,
  FIELD_ORDER,
  MAX_FILES,
  MESSAGES,
  fileKind,
  formatSize,
  validateFile,
  validateForm,
} from './validation'

/* Public form "Paraqit kërkesë ose ankesë" (Figma 44:2). No login. */

const TYPES = [
  {
    value: 'kerkese',
    title: 'Kërkesë',
    text: 'Kërkoni një shërbim, leje ose veprim nga inspektorati (p.sh. leje për shfrytëzim hapësire).',
  },
  {
    value: 'ankese',
    title: 'Ankesë',
    text: 'Raportoni një problem ose shkelje që duhet të inspektohet (p.sh. zënie trotuari, ndërtim pa leje).',
  },
]

function nowLabel() {
  const date = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(date.getDate())}.${pad(date.getMonth() + 1)}.${date.getFullYear()} · ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function Section({ title, subtitle, children }) {
  return (
    <section className="flex flex-col gap-[18px] rounded-card-lg border border-line bg-white px-7 py-6">
      <div className="flex flex-col gap-1">
        <h2 className="text-tracker font-bold text-ink">{title}</h2>
        {subtitle && <p className="text-body text-ink-2">{subtitle}</p>}
      </div>
      {children}
    </section>
  )
}

function ErrorText({ id, children }) {
  return children ? (
    <p id={id} className="text-caption font-medium text-danger">
      {children}
    </p>
  ) : null
}

function TypeCard({ type, selected, onSelect }) {
  return (
    <label
      className={[
        'flex cursor-pointer gap-3.5 rounded-item px-[19px] py-[17px] transition-colors',
        selected ? 'border-[1.5px] border-primary bg-primary-tint/60' : 'border border-line bg-white hover:border-line-strong',
      ].join(' ')}
    >
      <input
        type="radio"
        name="lloji"
        value={type.value}
        checked={selected}
        onChange={() => onSelect(type.value)}
        className="peer sr-only"
      />
      <span
        aria-hidden="true"
        className={`mt-px flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-[1.5px] peer-focus-visible:ring-2 peer-focus-visible:ring-primary ${
          selected ? 'border-primary bg-white' : 'border-line-strong bg-white'
        }`}
      >
        {selected && <span className="h-2.5 w-2.5 rounded-full bg-primary" />}
      </span>
      <span className="flex flex-col gap-1">
        <span className={`text-card-title font-semibold ${selected ? 'text-primary' : 'text-ink'}`}>{type.title}</span>
        <span className="text-meta leading-[17px] text-ink-2">{type.text}</span>
      </span>
    </label>
  )
}

function FileRow({ file, onRemove }) {
  const Icon = fileKind(file) === 'Foto' ? ImageIcon : FileText

  function download() {
    // The file is still only in the browser: download it from memory.
    const url = URL.createObjectURL(file)
    const link = document.createElement('a')
    link.href = url
    link.download = file.name
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  return (
    <li className="flex items-center gap-3 rounded-item border border-line px-[15px] py-[13px]">
      <span className="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-btn-lg bg-primary-tint text-primary">
        <Icon size={18} strokeWidth={1.75} />
      </span>
      <span className="flex min-w-0 flex-1 flex-col gap-0.5">
        <span className="truncate text-body font-semibold text-ink">{file.name}</span>
        <span className="text-caption text-ink-2">
          {fileKind(file)} · {formatSize(file.size)}
        </span>
      </span>
      <button
        type="button"
        onClick={download}
        className="inline-flex items-center gap-1.5 rounded-sm bg-primary-tint px-3 py-2 text-meta font-semibold text-primary hover:bg-primary hover:text-white"
      >
        <Download size={14} strokeWidth={2} />
        Shkarko
      </button>
      <button
        type="button"
        onClick={onRemove}
        aria-label={`Hiq ${file.name}`}
        className="flex h-7 w-7 items-center justify-center rounded-sm text-ink-3 hover:bg-neutral-tint hover:text-ink"
      >
        <X size={16} strokeWidth={1.75} />
      </button>
    </li>
  )
}

export default function KerkesaForm() {
  const navigate = useNavigate()
  const fileInput = useRef(null)
  const [values, setValues] = useState(EMPTY_FORM)
  const [files, setFiles] = useState([])
  const [errors, setErrors] = useState({})
  const [fileError, setFileError] = useState('')
  const [serverError, setServerError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [now, setNow] = useState(nowLabel)

  // The submission date is shown live; the server records the exact time.
  useEffect(() => {
    const timer = setInterval(() => setNow(nowLabel()), 30_000)
    return () => clearInterval(timer)
  }, [])

  const fullName = `${values.emri.trim()} ${values.mbiemri.trim()}`.trim()

  function set(field, value) {
    setValues((current) => ({ ...current, [field]: value }))
    if (errors[field]) setErrors((current) => ({ ...current, [field]: undefined }))
  }

  const bind = (field) => ({
    id: field,
    name: field,
    value: values[field],
    onChange: (event) => set(field, event.target.value),
    invalid: !!errors[field],
    'aria-invalid': !!errors[field],
  })

  function addFiles(list) {
    const added = []
    const problems = []
    for (const file of list) {
      const problem = validateFile(file)
      if (problem) problems.push(`${file.name}: ${problem}`)
      else added.push(file)
    }
    const room = MAX_FILES - files.length
    if (added.length > room) problems.push(MESSAGES.tooManyFiles)
    setFiles((current) => [...current, ...added.slice(0, Math.max(0, room))])
    setFileError(problems.join(' · '))
  }

  function onPick(event) {
    addFiles([...event.target.files])
    event.target.value = '' // so the same file can be picked again after removing it
  }

  function onDrop(event) {
    event.preventDefault()
    setDragging(false)
    addFiles([...event.dataTransfer.files])
  }

  function clearForm() {
    setValues(EMPTY_FORM)
    setFiles([])
    setErrors({})
    setFileError('')
    setServerError('')
  }

  function focusFirstError(found) {
    const first = FIELD_ORDER.find((field) => found[field])
    const element = first && document.getElementById(first === 'lloji' ? 'lloji-zgjedhje' : first)
    element?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    element?.focus?.({ preventScroll: true })
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setServerError('')
    const found = validateForm(values)
    setErrors(found)
    if (Object.keys(found).length > 0) {
      focusFirstError(found)
      return
    }

    const body = new FormData()
    for (const [field, value] of Object.entries(values)) {
      body.append(field, typeof value === 'boolean' ? String(value) : value.trim())
    }
    for (const file of files) body.append('files', file)

    setSubmitting(true)
    try {
      const { data } = await api.post('/kerkesa', body)
      navigate(`/kerkese/konfirmim/${data.numri_gjurmimit}`, { state: { lloji: values.lloji } })
    } catch (err) {
      const detail = err.response?.status === 422 ? err.response.data?.detail : null
      if (Array.isArray(detail)) {
        // Show the server's messages next to the matching fields.
        const fromServer = {}
        for (const item of detail) {
          const field = item.loc?.[1]
          const message = item.msg.replace(/^Value error, /, '')
          if (field === 'files') setFileError(message)
          else if (field) fromServer[field] = message
        }
        setErrors(fromServer)
        focusFirstError(fromServer)
      } else {
        setServerError(errorMessage(err))
      }
      setSubmitting(false)
    }
  }

  const hasErrors = Object.values(errors).some(Boolean)

  return (
    <div className="min-h-screen bg-page">
      <PublicHeader />
      <main className="mx-auto max-w-[840px] px-4 pt-10 pb-16">
        <div className="flex flex-col items-start gap-2">
          <span className="rounded-pill bg-primary-tint px-3 py-[5px] text-caption font-semibold text-primary">
            Shërbim publik · pa llogari
          </span>
          <h1 className="text-heading font-bold text-ink">Paraqit kërkesë ose ankesë</h1>
          <p className="text-body-lg leading-[21px] text-ink-2">
            Plotësoni formularin më poshtë. Fushat me <span className="text-danger">*</span> janë të detyrueshme. Pas
            dërgimit merrni një numër gjurmimi për të ndjekur statusin.
          </p>
        </div>

        <form onSubmit={handleSubmit} noValidate className="mt-5 flex flex-col gap-5">
          <Section title="1. Lloji i paraqitjes" subtitle="Zgjidhni çfarë po paraqisni. Data plotësohet automatikisht.">
            <div
              id="lloji-zgjedhje"
              tabIndex={-1}
              role="radiogroup"
              aria-label="Lloji i paraqitjes"
              className="grid gap-3.5 outline-none sm:grid-cols-2"
            >
              {TYPES.map((type) => (
                <TypeCard key={type.value} type={type} selected={values.lloji === type.value} onSelect={(v) => set('lloji', v)} />
              ))}
            </div>
            <ErrorText id="lloji-error">{errors.lloji}</ErrorText>
            <div className="flex items-center gap-3 rounded-btn-lg bg-page px-3.5 py-3">
              <CalendarDays size={18} strokeWidth={1.75} className="text-ink-2" />
              <div className="flex flex-1 flex-col">
                <span className="text-caption text-ink-2">Data e paraqitjes</span>
                <span className="text-body font-semibold text-ink" data-testid="data-paraqitjes">
                  {now}
                </span>
              </div>
              <span className="rounded-tag bg-primary-tint px-2 py-1 text-eyebrow font-bold text-primary">automatik</span>
            </div>
          </Section>

          <Section title="2. Të dhënat e aplikuesit" subtitle="Identiteti juaj është i nevojshëm për deklaratën e vërtetësisë në fund.">
            <div className="grid gap-x-4 gap-y-[18px] sm:grid-cols-2">
              <Field label="Emri" required htmlFor="emri" error={errors.emri}>
                <Input {...bind('emri')} autoComplete="given-name" placeholder="Emri juaj" />
              </Field>
              <Field label="Mbiemri" required htmlFor="mbiemri" error={errors.mbiemri}>
                <Input {...bind('mbiemri')} autoComplete="family-name" placeholder="Mbiemri juaj" />
              </Field>
              <Field label="Numri personal" required htmlFor="numri_personal" error={errors.numri_personal} hint="10 shifra, sipas letërnjoftimit">
                <Input {...bind('numri_personal')} inputMode="numeric" maxLength={11} placeholder="p.sh. 1234567890" />
              </Field>
              <Field label="Email" htmlFor="email" error={errors.email} hint="Opsional — për njoftime me email">
                <Input {...bind('email')} type="email" autoComplete="email" placeholder="ju@example.com" />
              </Field>
              <Field label="Numri i telefonit" required htmlFor="telefoni" error={errors.telefoni}>
                <Input {...bind('telefoni')} type="tel" autoComplete="tel" placeholder="+383 44 000 000" />
              </Field>
              <Field label="Adresa e banimit" htmlFor="adresa" error={errors.adresa}>
                <Input {...bind('adresa')} autoComplete="street-address" placeholder="Rruga, numri, lagjja, qyteti" />
              </Field>
            </div>
          </Section>

          <Section title="3. Detajet e rastit">
            <div className="flex">
              <span className="rounded-sm bg-primary-tint px-3 py-2 text-meta text-primary" data-testid="lloji-zgjedhur">
                Lloji i zgjedhur: <span className="font-bold">{LLOJI_LABEL[values.lloji] ?? '—'}</span>
              </span>
            </div>
            <Field label="Lokacioni i rastit" required htmlFor="lokacioni" error={errors.lokacioni} hint="Sa më i saktë, aq më shpejt del inspektori në terren">
              <Input {...bind('lokacioni')} placeholder="Lagjja, rruga ose pika e referimit ku ndodhi" />
            </Field>
            <Field label="Përshkrimi i rastit" required htmlFor="pershkrimi" error={errors.pershkrimi} hint="Shkruani lirshëm — sistemi e strukturon vetë përmbajtjen.">
              <Textarea {...bind('pershkrimi')} placeholder="Përshkruani problemin me fjalët tuaja: çfarë, ku, kur dhe kush është i përfshirë…" />
            </Field>
          </Section>

          <Section
            title="4. Dokumente dhe foto shtesë"
            subtitle="Opsionale. Bashkangjitni foto ose dokumente që e mbështesin rastin (PDF, JPG, PNG · deri 10 MB secili)."
          >
            <input
              ref={fileInput}
              id="files"
              type="file"
              multiple
              accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
              onChange={onPick}
              className="sr-only"
              tabIndex={-1}
            />
            <button
              type="button"
              onClick={() => fileInput.current?.click()}
              onDragOver={(event) => {
                event.preventDefault()
                setDragging(true)
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              className={`flex h-[122px] flex-col items-center justify-center gap-2 rounded-item border-[1.5px] border-dashed border-primary transition-colors ${
                dragging ? 'bg-primary-tint' : 'bg-white hover:bg-primary-tint/40'
              }`}
            >
              <Upload size={26} strokeWidth={1.75} className="text-primary" />
              <span className="text-body font-semibold text-ink">Tërhiq skedarët këtu ose kliko për të ngarkuar</span>
              <span className="text-caption text-ink-3">PDF, JPG, PNG — maksimumi 10 MB për skedar</span>
            </button>
            <ErrorText id="files-error">{fileError}</ErrorText>

            {files.length > 0 && (
              <div className="flex flex-col gap-3">
                <span className="text-eyebrow font-bold text-ink-2 uppercase">Skedarët e bashkangjitur ({files.length})</span>
                <ul className="flex flex-col gap-3">
                  {files.map((file, index) => (
                    <FileRow
                      key={`${file.name}-${file.size}-${index}`}
                      file={file}
                      onRemove={() => setFiles((current) => current.filter((_, i) => i !== index))}
                    />
                  ))}
                </ul>
              </div>
            )}
          </Section>

          <Section title="5. Dëshmia e aplikuesit për vërtetësi">
            <div className="rounded-item border border-line bg-quote px-[21px] py-[19px]" data-testid="deklarata">
              <p className="text-card-title font-bold text-ink">Unë, {fullName || '…'},</p>
              <p className="mt-1 text-body-lg text-ink">
                vërtetoj se informatat e lartshënuara janë të vërteta dhe të sakta, dhe marr përgjegjësi të plotë për to.
              </p>
            </div>
            <p className="-mt-1 text-caption text-ink-3">Emri plotësohet automatikisht nga të dhënat e aplikuesit.</p>
            <label className="flex cursor-pointer items-start gap-3">
              <input
                id="deklarata_pranuar"
                type="checkbox"
                checked={values.deklarata_pranuar}
                onChange={(event) => set('deklarata_pranuar', event.target.checked)}
                className="peer sr-only"
              />
              <span
                aria-hidden="true"
                className={`flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-tag border-[1.5px] peer-focus-visible:ring-2 peer-focus-visible:ring-primary ${
                  values.deklarata_pranuar
                    ? 'border-primary bg-primary text-white'
                    : errors.deklarata_pranuar
                      ? 'border-danger bg-white'
                      : 'border-line-strong bg-white'
                }`}
              >
                {values.deklarata_pranuar && <Check size={14} strokeWidth={3} />}
              </span>
              <span className="pt-0.5 text-body font-medium text-ink">
                Pajtohem me deklaratën e mësipërme dhe konfirmoj saktësinë e të dhënave.
              </span>
            </label>
            <ErrorText id="deklarata-error">{errors.deklarata_pranuar}</ErrorText>
          </Section>

          {hasErrors && <Alert>Kontrolloni fushat e shënuara me të kuqe dhe provoni përsëri.</Alert>}
          {serverError && <Alert>{serverError}</Alert>}

          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              type="submit"
              disabled={submitting}
              className="h-[50px] flex-1 rounded-btn-lg bg-primary text-card-title font-bold text-white hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submitting ? 'Duke dërguar…' : 'Konfirmo dhe dërgo'}
            </button>
            <button
              type="button"
              onClick={clearForm}
              className="h-[50px] rounded-btn-lg border border-line bg-white px-6 text-body-lg font-semibold text-ink hover:bg-sunken"
            >
              Pastro formularin
            </button>
          </div>

          <p className="flex items-center justify-center gap-2 text-center text-caption text-ink-2">
            <Lock size={13} strokeWidth={2} />
            Të dhënat tuaja përdoren vetëm për trajtimin e kësaj paraqitjeje. Pas dërgimit merrni një numër gjurmimi.
          </p>
        </form>
      </main>
    </div>
  )
}
