import { Check } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, errorMessage } from '../../api/client'
import PublicHeader from '../../components/PublicHeader'
import { Alert, Pill } from '../../components/ui'
import { dateTime } from '../../utils/date'
import { LLOJI_LABEL, PUBLIC_STATUS, TRACKING_PATTERN } from './status'

/* Public "Gjurmo kërkesën" page (Figma 25:2): status + timeline by tracking number. */

function when(value) {
  if (!value) return ''
  const date = new Date(value)
  const today = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  if (date.toDateString() === today.toDateString()) return `sot ${pad(date.getHours())}:${pad(date.getMinutes())}`
  return dateTime(value)
}

const STEP_META = { kryer: 'përfunduar', aktual: 'në proces', pritje: 'në pritje' }

function Step({ step }) {
  const done = step.gjendja === 'kryer'
  const current = step.gjendja === 'aktual'
  return (
    <li className="flex gap-3.5 py-1.5" data-state={step.gjendja}>
      <span className="flex h-[22px] w-[22px] shrink-0 items-center justify-center">
        <span
          className={`flex h-4 w-4 items-center justify-center rounded-full ${
            done ? 'bg-success text-white' : current ? 'bg-primary' : 'bg-line'
          }`}
        >
          {done && <Check size={10} strokeWidth={3.5} />}
        </span>
      </span>
      <span className="flex flex-col gap-px">
        <span className={`text-body-lg ${done || current ? 'font-semibold text-ink' : 'font-medium text-ink-2'}`}>
          {step.titulli}
        </span>
        <span className="text-meta text-ink-2">{done && step.koha ? when(step.koha) : STEP_META[step.gjendja]}</span>
      </span>
    </li>
  )
}

export default function Gjurmo() {
  const { numri: fromUrl } = useParams()
  const navigate = useNavigate()
  const [input, setInput] = useState(fromUrl ?? '')
  // The result belongs to the number it was loaded for.
  const [loaded, setLoaded] = useState({ numri: null, data: null, error: '' })

  const wanted = fromUrl?.trim().toUpperCase() ?? ''
  const valid = TRACKING_PATTERN.test(wanted)

  useEffect(() => {
    if (!valid) return
    let active = true
    api
      .get(`/kerkesa/gjurmo/${wanted}`)
      .then((response) => active && setLoaded({ numri: wanted, data: response.data, error: '' }))
      .catch((err) => active && setLoaded({ numri: wanted, data: null, error: errorMessage(err) }))
    return () => {
      active = false
    }
  }, [wanted, valid])

  const current = loaded.numri === wanted ? loaded : { data: null, error: '' }
  const loading = valid && loaded.numri !== wanted
  const formatError = fromUrl && !valid ? 'Shkruani numrin në formatin VU-2026-0001' : ''
  const result = current.data
  const status = result && (PUBLIC_STATUS[result.status] ?? { label: result.status, tone: 'neutral' })

  function handleSubmit(event) {
    event.preventDefault()
    navigate(`/gjurmo/${input.trim().toUpperCase()}`)
  }

  return (
    <div className="flex min-h-screen flex-col bg-page">
      <PublicHeader />
      <main className="mx-auto flex w-full max-w-[640px] flex-1 flex-col justify-center gap-[18px] px-4 py-12">
        <h1 className="text-heading font-bold text-ink">Gjurmo kërkesën tënde</h1>

        <form onSubmit={handleSubmit} className="flex gap-2.5">
          <input
            id="numri"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="VU-2026-0001"
            aria-label="Numri i gjurmimit"
            autoComplete="off"
            className="h-[46px] min-w-0 flex-1 rounded-btn-lg border-[1.5px] border-line bg-white px-3.5 text-body-lg font-semibold text-ink outline-none placeholder:font-normal placeholder:text-ink-3 focus:border-primary focus:ring-[3px] focus:ring-primary/15"
          />
          <button
            type="submit"
            disabled={!input.trim()}
            className="h-[46px] rounded-btn-lg bg-primary px-6 text-body-lg font-semibold text-white hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
          >
            Gjurmo
          </button>
        </form>

        {formatError && <Alert>{formatError}</Alert>}
        {current.error && <Alert>{current.error}</Alert>}
        {loading && <p className="text-meta text-ink-2">Duke kërkuar…</p>}

        {result && (
          <section className="rounded-card-lg border border-line bg-white px-[26px] pt-[22px] pb-6" data-testid="rezultati">
            <div className="flex items-center gap-3">
              <h2 className="text-tracker font-bold text-ink">
                {LLOJI_LABEL[result.lloji]} {result.numri_gjurmimit}
              </h2>
              <div className="flex-1" />
              <Pill tone={status.tone}>{status.label.toUpperCase()}</Pill>
            </div>
            <p className="mt-1 text-body text-ink-2">Paraqitur më {dateTime(result.created_at)}</p>
            <ol className="mt-3 flex flex-col">
              {result.timeline.map((step) => (
                <Step key={step.titulli} step={step} />
              ))}
            </ol>
          </section>
        )}
      </main>
    </div>
  )
}
