import { Link } from 'react-router-dom'

/* Small building blocks that follow the design specification (section 6). */

const BUTTON_VARIANTS = {
  primary: 'bg-primary text-white hover:bg-primary-hover',
  secondary: 'bg-white border border-line text-ink-2 hover:bg-sunken hover:border-line-strong',
  destructive: 'bg-white border border-danger text-danger hover:bg-danger-bg',
  soft: 'bg-page border border-line text-primary hover:bg-neutral-tint',
}

const BUTTON_SIZES = {
  sm: 'text-meta px-4 py-[9px] rounded-sm',
  md: 'text-body px-4 py-3 rounded-btn',
  lg: 'text-body-lg px-6 py-[13px] rounded-btn-lg',
}

/** Button, or a router link styled as a button when `to` is given. */
export function Button({ variant = 'primary', size = 'md', to, className = '', ...props }) {
  const classes = [
    'inline-flex items-center justify-center gap-2 font-semibold leading-none whitespace-nowrap',
    'transition-colors disabled:cursor-not-allowed disabled:opacity-50',
    BUTTON_VARIANTS[variant],
    BUTTON_SIZES[size],
    className,
  ].join(' ')

  if (to) {
    return <Link to={to} className={classes} {...props} />
  }
  return <button type="button" className={classes} {...props} />
}

export function Card({ className = '', children }) {
  return (
    <div className={`flex flex-col gap-3.5 rounded-card border border-line bg-white px-5 py-[18px] ${className}`}>
      {children}
    </div>
  )
}

const PILL_TONES = {
  teal: 'bg-primary-tint text-primary',
  amber: 'bg-warning-bg text-warning',
  red: 'bg-danger-bg text-danger',
  green: 'bg-success-bg text-success',
  neutral: 'bg-neutral-tint text-ink-2',
}

export function Pill({ tone = 'neutral', children }) {
  return (
    <span className={`inline-flex items-center justify-center rounded-pill px-2.5 py-1 text-caption font-semibold ${PILL_TONES[tone]}`}>
      {children}
    </span>
  )
}

/** The coat of arms (stema), used as the logo everywhere. `className` sets its height. */
export function Stema({ className = 'h-9' }) {
  return <img src="/stema.svg" alt="Stema" className={`w-auto shrink-0 ${className}`} />
}

/** Form field: label above the control, optional hint or error below. */
export function Field({ label, optional, required, error, hint, htmlFor, children }) {
  return (
    <div className="flex flex-col gap-[7px]">
      <label htmlFor={htmlFor} className="text-meta font-semibold text-ink">
        {label}
        {required && <span className="text-danger"> *</span>}
        {optional && <span className="font-normal text-ink-2"> (opsionale)</span>}
      </label>
      {children}
      {error && <p className="text-caption font-medium text-danger">{error}</p>}
      {!error && hint && <p className="text-caption text-ink-2">{hint}</p>}
    </div>
  )
}

const CONTROL =
  'w-full rounded-btn border border-line bg-sunken px-3.5 py-3 text-body text-ink outline-none ' +
  'placeholder:text-ink-3 focus:border-primary focus:bg-white focus:ring-[3px] focus:ring-primary/15 ' +
  'disabled:bg-neutral-tint disabled:text-ink-3'

export function Input({ invalid, className = '', ...props }) {
  return <input className={`${CONTROL} ${invalid ? 'border-danger' : ''} ${className}`} {...props} />
}

export function Textarea({ invalid, className = '', ...props }) {
  return <textarea className={`${CONTROL} h-[120px] resize-y ${invalid ? 'border-danger' : ''} ${className}`} {...props} />
}

export function Select({ invalid, className = '', children, ...props }) {
  return (
    <select className={`${CONTROL} ${invalid ? 'border-danger' : ''} ${className}`} {...props}>
      {children}
    </select>
  )
}

const ALERT_TONES = {
  red: 'bg-danger-bg text-danger',
  amber: 'bg-warning-bg text-warning',
  green: 'bg-success-bg text-success',
  teal: 'bg-primary-tint text-primary',
}

const DOT_TONES = {
  red: 'bg-danger',
  amber: 'bg-warning',
  green: 'bg-success',
  teal: 'bg-primary',
}

/** Banner with a status dot (spec 6.7), used for form errors and confirmations. */
export function Alert({ tone = 'red', onClose, children }) {
  return (
    <div role={tone === 'red' ? 'alert' : 'status'} className={`flex items-start gap-2 rounded-sm px-3 py-[9px] ${ALERT_TONES[tone]}`}>
      <span className={`mt-[5px] h-[7px] w-[7px] shrink-0 rounded-full ${DOT_TONES[tone]}`} />
      <span className="flex-1 text-meta leading-[17px] font-medium">{children}</span>
      {onClose && (
        <button type="button" onClick={onClose} aria-label="Mbyll" className="-my-0.5 px-1 text-body leading-none opacity-70 hover:opacity-100">
          ×
        </button>
      )}
    </div>
  )
}
