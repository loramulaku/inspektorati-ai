import { Link } from 'react-router-dom'
import BrandName from '../components/BrandName'
import { Stema } from '../components/ui'

/* Public landing page. Layout follows the reference screenshot: dark hero,
   centred two-line headline, two CTAs. Citizens never need an account. */

export default function Landing() {
  return (
    <div
      className="flex min-h-screen flex-col bg-civic-night"
      style={{
        backgroundImage:
          'radial-gradient(ellipse 70% 60% at 85% 10%, rgba(37, 99, 235, 0.16), transparent 60%),' +
          'radial-gradient(ellipse 60% 50% at 10% 95%, rgba(79, 70, 229, 0.10), transparent 60%)',
      }}
    >
      <header className="border-b border-white/[0.06]">
        <div className="mx-auto flex h-20 max-w-[1340px] items-center gap-4 px-4 sm:px-8">
          <Link to="/" className="flex items-center gap-3">
            <Stema className="h-10" />
            <BrandName className="text-[22px]" />
          </Link>

          <nav className="hidden flex-1 justify-center gap-8 md:flex">
            <span className="border-b-2 border-civic-sky pt-1 pb-2 text-[17px] font-medium text-civic-sky">Kreu</span>
            <Link to="/kerkese" className="pt-1 pb-2 text-[17px] text-slate-300 hover:text-white">
              Paraqit kërkesë
            </Link>
            <Link to="/gjurmo" className="pt-1 pb-2 text-[17px] text-slate-300 hover:text-white">
              Gjurmo kërkesën
            </Link>
          </nav>
          <div className="flex-1 md:hidden" />

          <Link
            to="/kycu"
            className="rounded-sm bg-civic-blue px-5 py-2.5 text-[17px] font-semibold text-white hover:bg-civic-blue-hover"
          >
            Kyçu si zyrtar
          </Link>
        </div>
      </header>

      <main className="flex flex-1 flex-col items-center px-4 pt-24 pb-16 text-center sm:pt-[140px]">
        <p className="text-[17px] font-medium text-civic-sky">Inspektorati komunal · Komuna e Vushtrrisë</p>

        <h1 className="mt-6 text-[48px] leading-[1.05] font-black tracking-[-0.02em] sm:text-[80px]">
          <span className="block text-slate-100">Raporto problemin.</span>
          <span className="block text-civic-blue">Inspektorati vepron.</span>
        </h1>

        <p className="mt-7 max-w-[720px] text-[19px] leading-[1.5] text-slate-400 sm:text-[23px]">
          Paraqitni kërkesë ose ankesë pa llogari, ndiqni statusin me numrin e gjurmimit — inspektorët veprojnë
          me ndihmën e AI-së.
        </p>

        <div className="mt-12 flex flex-col gap-4 sm:flex-row">
          <Link
            to="/kerkese"
            className="inline-flex h-[62px] items-center justify-center gap-3 rounded-xl bg-civic-blue px-10 text-[17px] font-bold text-white hover:bg-civic-blue-hover"
          >
            Paraqit kërkesë / ankesë si qytetar <span aria-hidden="true">→</span>
          </Link>
          <Link
            to="/kycu"
            className="inline-flex h-[62px] items-center justify-center rounded-xl border border-slate-600/50 bg-slate-800/50 px-10 text-[17px] font-bold text-slate-100 hover:bg-slate-800"
          >
            Kyçu si zyrtar
          </Link>
        </div>

        {/* AI highlight: frontend only, no backend logic behind it yet. */}
        <div className="mt-10 inline-flex items-center gap-2.5 rounded-full border border-civic-sky/25 bg-civic-blue/10 py-2 pr-4 pl-2">
          <span className="rounded-full bg-civic-blue px-2 py-0.5 text-[11px] font-bold text-white">AI</span>
          <span className="text-[14px] font-medium text-slate-200">
            Mbështetje nga AI për kategorizim dhe propozim vendimi
          </span>
        </div>

        <p className="mt-6 text-[13px] text-slate-500">Llogaritë krijohen nga administratori i inspektoratit.</p>
      </main>
    </div>
  )
}
