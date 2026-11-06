import { useEffect, useState } from 'react'
import { api, errorMessage } from '../api/client'
import { ROLE_LABEL } from '../auth/roles'
import { useAuth } from '../auth/useAuth'
import AppShell from '../components/AppShell'
import { Alert, Button, Card, Pill } from '../components/ui'
import { longDate } from '../utils/date'

/**
 * Placeholder dashboard for each role. It calls the role's protected API route
 * (/inspektor/paneli, /drejtor/paneli, /admin/paneli) to prove access works.
 */
export default function Dashboard({ role }) {
  const { user, welcome, dismissWelcome } = useAuth()
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  // Keep this page's copy of the post-login greeting, and clear the shared one
  // so it does not come back when the user returns to the dashboard later.
  const [greeting, setGreeting] = useState(welcome)

  useEffect(() => {
    if (welcome) dismissWelcome()
  }, [welcome, dismissWelcome])

  useEffect(() => {
    api
      .get(`/${role}/paneli`)
      .then((response) => setResult(response.data))
      .catch((err) => setError(errorMessage(err)))
  }, [role])

  return (
    <AppShell title="Paneli" subtitle={`Përmbledhje e ditës · ${longDate()}`}>
      {greeting && (
        <Alert tone="green" onClose={() => setGreeting(null)}>
          {greeting}
        </Alert>
      )}
      <div className="flex flex-col gap-5 lg:flex-row">
        <Card className="flex-1">
          <div className="flex items-center gap-2">
            <h2 className="text-card-title font-bold text-ink">Mirë se vini, {user.emri}</h2>
            <div className="flex-1" />
            <Pill tone="teal">{ROLE_LABEL[user.role].toUpperCase()}</Pill>
          </div>
          <p className="text-body text-ink">
            Moduli i panelit për rolin {ROLE_LABEL[user.role].toLowerCase()} do të ndërtohet në fazat e ardhshme.
            Tani për tani kjo faqe konfirmon që kyçja dhe qasja sipas rolit funksionojnë.
          </p>
          {role === 'admin' && (
            <div>
              <Button to="/admin/perdoruesit" size="sm">
                Menaxho përdoruesit →
              </Button>
            </div>
          )}
        </Card>

        <Card className="lg:w-[360px]">
          <div className="flex items-center">
            <h2 className="text-card-title font-bold text-ink">Qasja në API</h2>
            <div className="flex-1" />
            {result && <Pill tone="green">LEJUAR</Pill>}
            {error && <Pill tone="red">REFUZUAR</Pill>}
          </div>
          {!result && !error && <p className="text-meta text-ink-2">Duke kontrolluar…</p>}
          {error && <Alert>{error}</Alert>}
          {result && (
            <dl className="flex flex-col gap-2.5">
              {[
                ['Rruga', `GET /${role}/paneli`],
                ['Paneli', result.paneli],
                ['Mesazhi', result.mesazh],
                ['Roli', ROLE_LABEL[result.role]],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between gap-3">
                  <dt className="text-meta text-ink-2">{label}</dt>
                  <dd className="text-right text-meta font-semibold text-ink">{value}</dd>
                </div>
              ))}
            </dl>
          )}
        </Card>
      </div>
    </AppShell>
  )
}
