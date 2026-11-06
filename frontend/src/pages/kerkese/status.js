// Public wording for the request statuses (design spec 6.3 colour mapping).
export const PUBLIC_STATUS = {
  e_re: { label: 'E re', tone: 'teal' },
  kategorizuar: { label: 'Në shqyrtim', tone: 'amber' },
  caktuar: { label: 'Në shqyrtim', tone: 'amber' },
  ne_terren: { label: 'Në terren', tone: 'teal' },
  procesverbal: { label: 'Në terren', tone: 'teal' },
  vendim_propozuar: { label: 'Vendim', tone: 'amber' },
  vendim_miratuar: { label: 'Vendim', tone: 'amber' },
  mase_aktive: { label: 'Vendim', tone: 'amber' },
  riinspektim: { label: 'Vendim', tone: 'amber' },
  ankese: { label: 'Në shqyrtim', tone: 'amber' },
  mbyllur: { label: 'Zgjidhur', tone: 'green' },
}

export const LLOJI_LABEL = { kerkese: 'Kërkesë', ankese: 'Ankesë' }

export const TRACKING_PATTERN = /^VU-\d{4}-\d{4,}$/
