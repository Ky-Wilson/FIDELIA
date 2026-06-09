export default function ToolResult({ tool, data }) {
  if (!data || !data.success) return null

  if (tool === 'convert_currency') return (
    <div className="mt-2 bg-white/5 rounded-xl p-3 text-sm space-y-1">
      <div className="flex justify-between"><span className="text-gray-400">Montant</span><span>{data.amount?.toLocaleString()} {data.from_currency}</span></div>
      <div className="flex justify-between"><span className="text-gray-400">Taux</span><span className="text-amber-400">1 {data.from_currency} = {data.rate} {data.to_currency}</span></div>
      <div className="flex justify-between font-medium border-t border-white/10 pt-1"><span>Converti</span><span className="text-green-400">{data.converted_amount?.toLocaleString()} {data.to_currency}</span></div>
    </div>
  )

  if (tool === 'calculate_vat') return (
    <div className="mt-2 bg-white/5 rounded-xl p-3 text-sm space-y-1">
      <div className="flex justify-between"><span className="text-gray-400">Montant HT</span><span>{data.amount_ht?.toLocaleString()} FCFA</span></div>
      <div className="flex justify-between"><span className="text-gray-400">TVA ({data.tva_rate})</span><span className="text-amber-400">{data.tva_amount?.toLocaleString()} FCFA</span></div>
      <div className="flex justify-between font-medium border-t border-white/10 pt-1"><span>Total TTC</span><span className="text-green-400">{data.amount_ttc?.toLocaleString()} FCFA</span></div>
    </div>
  )

  if (tool === 'calculate_cnps') return (
    <div className="mt-2 bg-white/5 rounded-xl p-3 text-sm space-y-1">
      <div className="flex justify-between"><span className="text-gray-400">Base de cotisation</span><span>{data.base_cotisation?.toLocaleString()} FCFA</span></div>
      <div className="flex justify-between"><span className="text-gray-400">Part employeur</span><span className="text-red-400">{data.part_employeur?.total?.toLocaleString()} FCFA</span></div>
      <div className="flex justify-between"><span className="text-gray-400">Part salarié</span><span className="text-orange-400">{data.part_salarie?.total?.toLocaleString()} FCFA</span></div>
      <div className="flex justify-between font-medium border-t border-white/10 pt-1"><span>Total / employé</span><span className="text-green-400">{data.total_par_employe?.toLocaleString()} FCFA</span></div>
    </div>
  )

  if (tool === 'get_tax_deadlines') return (
    <div className="mt-2 bg-white/5 rounded-xl p-3 text-sm space-y-2 max-h-48 overflow-y-auto">
      {data.echeances?.slice(0, 5).map((e, i) => (
        <div key={i} className="flex justify-between items-center">
          <span className="text-gray-300">{e.nom}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${
            e.statut === 'urgent' ? 'bg-red-500/30 text-red-300' :
            e.statut === 'passé'  ? 'bg-gray-500/30 text-gray-400' :
                                    'bg-blue-500/30 text-blue-300'
          }`}>{e.date}</span>
        </div>
      ))}
    </div>
  )

  if (tool === 'search_tax_code') return (
    <div className="mt-2 bg-white/5 rounded-xl p-3 text-sm space-y-2 max-h-48 overflow-y-auto">
      {data.results?.slice(0, 3).map((r, i) => (
        <div key={i} className="border-b border-white/10 pb-2 last:border-0">
          <div className="text-blue-300 font-medium">{r.article} — {r.titre}</div>
          <div className="text-gray-400 text-xs mt-0.5">{r.texte}</div>
        </div>
      ))}
    </div>
  )

  return null
}