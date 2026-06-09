const TOOL_LABELS = {
  convert_currency: { label: 'Conversion devises',         color: 'bg-blue-500/20 text-blue-300 border-blue-500/30' },
  calculate_vat:    { label: 'Calcul TVA · CGI CI',         color: 'bg-green-500/20 text-green-300 border-green-500/30' },
  get_tax_deadlines:{ label: 'Échéances fiscales · DGI',    color: 'bg-amber-500/20 text-amber-300 border-amber-500/30' },
  calculate_cnps:   { label: 'Cotisations CNPS',            color: 'bg-purple-500/20 text-purple-300 border-purple-500/30' },
  search_tax_code:  { label: 'Code Général des Impôts CI',  color: 'bg-red-500/20 text-red-300 border-red-500/30' },
}

export default function ToolBadge({ tool }) {
  const info = TOOL_LABELS[tool]
  if (!info) return null
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs border ${info.color}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-70" />
      {info.label}
    </span>
  )
}