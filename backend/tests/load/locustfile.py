"""
Test de montée en charge pour FIDELIA.

Usage :
    pip install locust
    locust -f tests/load/locustfile.py --host http://localhost:8000

Puis ouvrir http://localhost:8089 pour piloter le test (nombre d'utilisateurs,
taux de spawn) et observer la latence / le taux d'erreur en fonction de la charge.

Les endpoints "outils" (déterministes, sans appel LLM) sont testés séparément
du endpoint /mcp/chat (appel OpenAI), car ce dernier est le principal goulot
d'étranglement attendu (latence + coût par appel LLM).
"""

from locust import HttpUser, task, between


class ToolsUser(HttpUser):
    """Simule un utilisateur qui interroge directement les outils MCP (sans LLM)."""

    wait_time = between(0.5, 2)

    @task(3)
    def calculate_vat(self):
        self.client.post("/mcp/tools/calculate_vat", json={"amount_ht": 100000, "tva_type": "TVA"})

    @task(2)
    def calculate_cnps(self):
        self.client.post("/mcp/tools/calculate_cnps", json={"salaire_brut": 300000, "nb_employes": 1})

    @task(2)
    def get_tax_deadlines(self):
        self.client.post("/mcp/tools/get_tax_deadlines", json={})

    @task(1)
    def search_tax_code(self):
        self.client.post("/mcp/tools/search_tax_code", json={"query": "TVA"})

    @task(1)
    def health(self):
        self.client.get("/health")


class ChatUser(HttpUser):
    """Simule un utilisateur du chat conversationnel (déclenche un appel OpenAI)."""

    wait_time = between(2, 5)

    @task
    def chat(self):
        self.client.post(
            "/mcp/chat",
            json={"messages": [{"role": "user", "content": "Calcule la TVA sur 100000 FCFA"}]},
        )
