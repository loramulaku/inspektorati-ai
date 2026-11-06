import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { errorMessage } from '../api/client'
import { ROLE_HOME } from '../auth/roles'
import { useAuth } from '../auth/useAuth'
import AuthLayout from '../components/AuthLayout'
import BrandName from '../components/BrandName'
import { Stema } from '../components/ui'

const INPUT =
  'h-12 w-full rounded-[10px] border border-[#263248] bg-[#0b1220] px-4 text-[15px] text-slate-100 outline-none ' +
  'placeholder:text-slate-500 focus:border-civic-blue focus:ring-[3px] focus:ring-civic-blue/20'

function EyeIcon({ open }) {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z" />
      <circle cx="12" cy="12" r="3" />
      {!open && <path d="M4 4l16 16" />}
    </svg>
  )
}

export default function Login() {
  const { user, login } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (user && !submitting) {
    return <Navigate to={ROLE_HOME[user.role]} replace />
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!email.trim() || !password) {
      setError('Shkruani email-in dhe fjalëkalimin.')
      return
    }
    setError('')
    setSubmitting(true)
    try {
      const loggedIn = await login(email.trim(), password)
      navigate(ROLE_HOME[loggedIn.role], { replace: true })
    } catch (err) {
      setError(errorMessage(err))
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout>
      <div className="w-full max-w-[440px] rounded-[22px] border border-white/10 bg-[#172036]/75 px-6 py-9 backdrop-blur sm:px-10 sm:py-10">
        <div className="flex items-center gap-3">
          <Stema className="h-9" />
          <BrandName className="text-[20px]" />
        </div>

        <h2 className="mt-7 text-[26px] font-bold text-slate-100">Mirë se vini</h2>
        <p className="mt-1 text-[15px] text-slate-400">Kyçuni në llogarinë tuaj të stafit</p>

        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-5" noValidate>
          {error && (
            <div role="alert" className="rounded-[10px] border border-red-500/30 bg-red-500/10 px-4 py-2.5 text-[14px] text-red-300">
              {error}
            </div>
          )}

          <div className="flex flex-col gap-2">
            <label htmlFor="email" className="text-[15px] font-semibold text-slate-200">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="emri@vushtrri.rks-gov.net"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={INPUT}
              required
            />
          </div>

          <div className="flex flex-col gap-2">
            <label htmlFor="password" className="text-[15px] font-semibold text-slate-200">
              Fjalëkalimi
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                placeholder="Fjalëkalimi juaj"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={`${INPUT} pr-12`}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword((shown) => !shown)}
                aria-label={showPassword ? 'Fshih fjalëkalimin' : 'Shfaq fjalëkalimin'}
                className="absolute inset-y-0 right-0 flex w-12 items-center justify-center text-slate-300 hover:text-white"
              >
                <EyeIcon open={showPassword} />
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="h-[52px] w-full rounded-[10px] bg-civic-blue text-[16px] font-bold text-white hover:bg-civic-blue-hover disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? 'Duke hyrë…' : 'Hyr'}
          </button>
        </form>

        <p className="mt-6 text-center text-[14px] text-slate-400">Llogaritë krijohen nga administratori i inspektoratit.</p>
        <p className="mt-3 text-center">
          <Link to="/" className="text-[13px] text-slate-400 hover:text-slate-200">
            ← Kthehu te faqja kryesore
          </Link>
        </p>
      </div>
    </AuthLayout>
  )
}
