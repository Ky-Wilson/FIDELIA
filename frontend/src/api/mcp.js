const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function callTool(toolName, payload) {
  const res = await fetch(`${BASE_URL}/mcp/tools/${toolName}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`Erreur ${res.status}`)
  return res.json()
}

export const mcpTools = {
  convertCurrency: (amount, from_currency, to_currency) => callTool('convert_currency', { amount, from_currency, to_currency }),
  calculateVat:    (amount_ht, tva_type) =>        callTool('calculate_vat', { amount_ht, tva_type }),
  getTaxDeadlines: (filter_type) =>               callTool('get_tax_deadlines', { filter_type }),
  calculateCnps:   (salaire_brut, nb_employes) => callTool('calculate_cnps', { salaire_brut, nb_employes }),
  searchTaxCode:   (query) =>                     callTool('search_tax_code', { query }),
}

// Tout passe par notre backend — clé OpenAI jamais exposée au browser
export async function sendMessage(conversationHistory) {
  const res = await fetch(`${BASE_URL}/mcp/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages: conversationHistory }),
  })
  if (!res.ok) {
    const body = await res.text()
    const error = new Error(`Erreur backend ${res.status}: ${body}`)
    error.status = res.status
    throw error
  }
  return res.json()
}