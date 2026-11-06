import { useCallback, useEffect, useState } from 'react'
import { api, errorMessage } from '../api/client'
import { ROLE_LABEL } from '../auth/roles'
import { useAuth } from '../auth/useAuth'
import AppShell from '../components/AppShell'
import { Alert, Button, Card, Field, Input, Pill, Select } from '../components/ui'
import { dateTime } from '../utils/date'

const ROLE_TONE = { inspektor: 'teal', drejtor: 'amber', admin: 'neutral' }
const EMPTY_FORM = { emri: '', mbiemri: '', email: '', role: 'inspektor', sektori_id: '', telefoni: '', password: '' }

/** Create or edit form shown in the right rail. `user` is null when creating. */
function UserForm({ user, sectors, onSaved, onCancel }) {
  const [form, setForm] = useState(() =>
    user
      ? {
          emri: user.emri,
          mbiemri: user.mbiemri,
          email: user.email,
          role: user.role,
          sektori_id: user.sektori_id ?? '',
          telefoni: user.telefoni ?? '',
          password: '',
        }
      : EMPTY_FORM,
  )
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  function update(field) {
    return (event) => setForm((current) => ({ ...current, [field]: event.target.value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSaving(true)
    const payload = {
      emri: form.emri.trim(),
      mbiemri: form.mbiemri.trim(),
      email: form.email.trim(),
      role: form.role,
      sektori_id: form.sektori_id ? Number(form.sektori_id) : null,
      telefoni: form.telefoni.trim() || null,
    }
    try {
      if (user) {
        await api.patch(`/admin/users/${user.id}`, payload)
      } else {
        await api.post('/admin/users', { ...payload, password: form.password })
      }
      onSaved(user ? 'Ndryshimet u ruajtën.' : `Llogaria për ${payload.emri} ${payload.mbiemri} u krijua.`)
    } catch (err) {
      setError(errorMessage(err))
      setSaving(false)
    }
  }

  return (
    <Card>
      <h2 className="text-card-title font-bold text-ink">{user ? 'Modifiko përdoruesin' : 'Shto përdorues'}</h2>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3.5" noValidate>
        {error && <Alert>{error}</Alert>}
        <div className="grid gap-3.5 md:grid-cols-3">
          <Field label="Emri" htmlFor="u-emri">
            <Input id="u-emri" value={form.emri} onChange={update('emri')} />
          </Field>
          <Field label="Mbiemri" htmlFor="u-mbiemri">
            <Input id="u-mbiemri" value={form.mbiemri} onChange={update('mbiemri')} />
          </Field>
          <Field label="Email" htmlFor="u-email">
            <Input id="u-email" type="email" value={form.email} onChange={update('email')} placeholder="emri@vushtrri.rks-gov.net" />
          </Field>
          <Field label="Roli" htmlFor="u-role">
            <Select id="u-role" value={form.role} onChange={update('role')}>
              {Object.entries(ROLE_LABEL).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Sektori" optional htmlFor="u-sektori">
            <Select id="u-sektori" value={form.sektori_id} onChange={update('sektori_id')} disabled={sectors.length === 0}>
              <option value="">{sectors.length === 0 ? 'Nuk ka sektorë ende' : '— Pa sektor —'}</option>
              {sectors.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.emri}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Telefoni" optional htmlFor="u-telefoni">
            <Input id="u-telefoni" value={form.telefoni} onChange={update('telefoni')} placeholder="044 123 456" />
          </Field>
          {!user && (
            <Field label="Fjalëkalimi fillestar" htmlFor="u-password" hint="Të paktën 8 karaktere">
              <Input id="u-password" type="password" autoComplete="new-password" value={form.password} onChange={update('password')} />
            </Field>
          )}
        </div>
        <div className="flex gap-2.5 md:max-w-[480px]">
          <Button type="submit" className="flex-1" disabled={saving}>
            {saving ? 'Duke ruajtur…' : user ? 'Ruaj ndryshimet' : 'Krijo llogarinë'}
          </Button>
          <Button variant="secondary" onClick={onCancel}>
            Anulo
          </Button>
        </div>
      </form>
    </Card>
  )
}

export default function AdminUsers() {
  const { user: me } = useAuth()
  const [users, setUsers] = useState([])
  const [sectors, setSectors] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  // null = no form, 'new' = create form, a user object = edit form
  const [editing, setEditing] = useState(null)

  const loadUsers = useCallback(() => {
    return api
      .get('/admin/users')
      .then((response) => setUsers(response.data))
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    loadUsers()
    api
      .get('/auth/sektoret')
      .then((response) => setSectors(response.data))
      .catch(() => setSectors([]))
  }, [loadUsers])

  const sectorName = (id) => sectors.find((s) => s.id === id)?.emri ?? '—'
  const activeCount = users.filter((u) => u.aktiv).length

  async function toggleActive(user) {
    setError('')
    setNotice('')
    try {
      if (user.aktiv) {
        if (!window.confirm(`Ta çaktivizoni llogarinë e ${user.emri} ${user.mbiemri}? Përdoruesi do të çkyçet menjëherë.`)) {
          return
        }
        await api.post(`/admin/users/${user.id}/deactivate`)
        setNotice(`Llogaria e ${user.emri} ${user.mbiemri} u çaktivizua.`)
      } else {
        await api.patch(`/admin/users/${user.id}`, { aktiv: true })
        setNotice(`Llogaria e ${user.emri} ${user.mbiemri} u aktivizua.`)
      }
      await loadUsers()
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  async function handleSaved(message) {
    setEditing(null)
    setNotice(message)
    await loadUsers()
  }

  return (
    <AppShell title="Përdoruesit & rolet" subtitle={`${users.length} përdorues · ${activeCount} aktivë`}>
      <div className="flex items-center gap-2.5">
        <div className="flex-1">
          {notice && <Alert tone="green">{notice}</Alert>}
          {error && <Alert>{error}</Alert>}
        </div>
        <Button onClick={() => { setNotice(''); setEditing('new') }}>+ Shto përdorues</Button>
      </div>

      {editing && (
        <UserForm
          key={editing === 'new' ? 'new' : editing.id}
          user={editing === 'new' ? null : editing}
          sectors={sectors}
          onSaved={handleSaved}
          onCancel={() => setEditing(null)}
        />
      )}

      <div className="overflow-x-auto rounded-card border border-line bg-white">
        <table className="w-full min-w-[760px] border-collapse text-left">
          <thead className="bg-sunken">
            <tr className="text-eyebrow font-bold text-ink-2 uppercase">
              <th className="px-5 py-[13px]">Emri</th>
              <th className="px-3 py-[13px]">Email</th>
              <th className="w-[100px] px-3 py-[13px] text-center">Roli</th>
              <th className="px-3 py-[13px]">Sektori</th>
              <th className="w-[100px] px-3 py-[13px] text-center">Statusi</th>
              <th className="px-5 py-[13px] text-right">Veprime</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={6} className="px-5 py-12 text-center text-meta text-ink-2">Duke u ngarkuar…</td>
              </tr>
            )}
            {users.map((u) => (
              <tr key={u.id} className="border-t border-line">
                <td className="px-5 py-3.5 whitespace-nowrap">
                  <div className="text-body font-semibold text-ink">
                    {u.emri} {u.mbiemri}
                    {u.id === me.id && <span className="font-normal text-ink-2"> (ju)</span>}
                  </div>
                  <div className="text-caption text-ink-2">Krijuar {dateTime(u.created_at)}</div>
                </td>
                <td className="px-3 py-3.5 text-meta text-ink-2">{u.email}</td>
                <td className="px-3 py-3.5 text-center">
                  <Pill tone={ROLE_TONE[u.role]}>{ROLE_LABEL[u.role]}</Pill>
                </td>
                <td className="px-3 py-3.5 text-meta text-ink-2">{sectorName(u.sektori_id)}</td>
                <td className="px-3 py-3.5 text-center">
                  <Pill tone={u.aktiv ? 'green' : 'neutral'}>{u.aktiv ? 'Aktiv' : 'Joaktiv'}</Pill>
                </td>
                <td className="px-5 py-3.5">
                  <div className="flex justify-end gap-2">
                    <Button size="sm" variant="secondary" onClick={() => { setNotice(''); setEditing(u) }}>
                      Modifiko
                    </Button>
                    {u.id !== me.id &&
                      (u.aktiv ? (
                        <Button size="sm" variant="destructive" onClick={() => toggleActive(u)}>
                          Çaktivizo
                        </Button>
                      ) : (
                        <Button size="sm" variant="soft" onClick={() => toggleActive(u)}>
                          Aktivizo
                        </Button>
                      ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AppShell>
  )
}
