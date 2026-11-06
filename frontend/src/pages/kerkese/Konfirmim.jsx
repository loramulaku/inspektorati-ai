import { Check } from 'lucide-react'
import { useLocation, useParams } from 'react-router-dom'
import PublicHeader from '../../components/PublicHeader'
import { Button } from '../../components/ui'

/* Confirmation after sending the form (Figma 24:99). */
export default function Konfirmim() {
  const { numri } = useParams()
  const location = useLocation()
  const title = location.state?.lloji === 'ankese' ? 'Ankesa u dërgua me sukses' : 'Kërkesa u dërgua me sukses'

  return (
    <div className="flex min-h-screen flex-col bg-page">
      <PublicHeader />
      <main className="flex flex-1 items-center justify-center px-4 py-12">
        <div className="flex w-full max-w-[516px] flex-col items-center gap-4 text-center">
          <div className="flex h-[72px] w-[72px] items-center justify-center rounded-full bg-success-bg text-success">
            <Check size={30} strokeWidth={2.5} />
          </div>
          <h1 className="mt-2 text-[26px] font-bold text-ink">{title}</h1>
          <p className="text-card-title text-ink-2">Faleminderit. Kërkesa juaj u pranua dhe po përpunohet nga sistemi.</p>

          <div className="mt-2 flex w-full flex-col items-center gap-1 rounded-card-lg border border-line bg-white px-6 py-5">
            <span className="text-eyebrow font-semibold text-ink-2 uppercase">Numri i gjurmimit</span>
            <span className="text-[32px] font-bold tracking-[-0.01em] text-primary" data-testid="numri-gjurmimit">
              {numri}
            </span>
            <span className="text-meta text-ink-2">Ruajeni këtë numër për të ndjekur statusin</span>
          </div>

          <div className="w-full rounded-item bg-primary-tint px-5 py-4 text-left">
            <p className="text-body font-bold text-primary">Çfarë ndodh më pas</p>
            <p className="mt-1.5 text-body leading-5 text-primary">
              Sistemi e kategorizon kërkesën → inspektori përkatës e verifikon në terren → ju njoftoheni për vendimin.
            </p>
          </div>

          <Button to={`/gjurmo/${numri}`} size="lg" className="mt-2">
            Gjurmo statusin tani
          </Button>
        </div>
      </main>
    </div>
  )
}
