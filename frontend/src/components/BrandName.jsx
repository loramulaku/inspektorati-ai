/** Product name in two tones ("Inspektorati" + blue "AI"), as on the reference screens. */
export default function BrandName({ className = '' }) {
  return (
    <span className={`font-bold tracking-[-0.01em] text-slate-100 ${className}`}>
      Inspektorati <span className="text-civic-blue">AI</span>
    </span>
  )
}
