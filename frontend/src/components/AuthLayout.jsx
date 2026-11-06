import BrandName from './BrandName'
import { Stema } from './ui'

const FEATURES = [
  { text: 'Kategorizim i asistuar nga AI', tag: 'AI' },
  { text: 'Lidhje me bazën ligjore', tag: 'RAG' },
  { text: 'Gjurmueshmëri e plotë e veprimeve' },
  { text: 'Procesverbali dhe vendimi në një vend' },
  { text: 'Vendimi dhe nënshkrimi mbeten te inspektori' },
]

function CheckIcon() {
  return (
    <svg viewBox="0 0 16 16" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M3.5 8.5l3 3 6-7" />
    </svg>
  )
}

/** Left half of the login screen: brand, headline, feature checklist. */
function BrandPanel() {
  return (
    <aside
      className="hidden w-1/2 shrink-0 flex-col px-12 pt-11 pb-10 lg:flex"
      style={{ background: 'linear-gradient(165deg, #2c3342 0%, #272d3b 55%, #2b2a44 100%)' }}
    >
      <div className="flex items-center gap-3">
        <Stema className="h-9" />
        <BrandName className="text-[20px]" />
      </div>

      <h1 className="mt-9 text-[40px] leading-[1.2] font-black tracking-[-0.02em] text-slate-100">
        Prano kërkesën.
        <br />
        Inspekto.
        <br />
        Vendos me ligj.
      </h1>

      <p className="mt-5 max-w-[460px] text-[16px] leading-[26px] text-slate-400">
        Kërkesat, inspektimet dhe vendimet e Komunës së Vushtrrisë, me mbështetjen e AI-së, në një vend.
      </p>

      <ul className="mt-8 flex flex-col gap-3.5">
        {FEATURES.map((feature) => (
          <li key={feature.text} className="flex items-center gap-3">
            <span className="flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-full bg-civic-blue/20 text-civic-sky">
              <CheckIcon />
            </span>
            <span className="text-[15px] text-slate-200">{feature.text}</span>
            {feature.tag && (
              <span className="rounded-md bg-civic-blue/20 px-1.5 py-0.5 text-[10px] font-bold text-civic-sky">
                {feature.tag}
              </span>
            )}
          </li>
        ))}
      </ul>

      <div className="flex-1" />
      <div className="mt-8 border-t border-slate-500/50 pt-5 text-[13px] text-slate-400">
        Llogaritë krijohen nga administratori i inspektoratit.
      </div>
    </aside>
  )
}

/** Split screen: brand panel on the left, the form card centred on the right. */
export default function AuthLayout({ children }) {
  return (
    <div className="flex min-h-screen">
      <BrandPanel />
      <main
        className="flex flex-1 items-center justify-center bg-civic-night px-4 py-10"
        style={{
          backgroundImage: 'radial-gradient(ellipse 80% 60% at 90% 0%, rgba(37, 99, 235, 0.14), transparent 60%)',
        }}
      >
        {children}
      </main>
    </div>
  )
}
