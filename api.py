from fastapi import FastAPI, HTTPException, Depends, Header
from google.cloud import bigquery
import os
import json
from datetime import datetime

# =============================================
# CONFIGURATION
# =============================================
app = FastAPI(title="Transfer Rates API", version="1.0")

PROJECT_ID = "crafty-coral-420410"
DATASET_ID = "transfert_data"
TABLE_ID = "taux_historiques"

# =============================================
# AUTHENTIFICATION BIGQUERY (SÉCURISÉE)
# =============================================
def get_bigquery_client():
    # En production (Render) : on lit la clé depuis la variable d'environnement
    if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in os.environ:
        creds = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
        return bigquery.Client.from_service_account_info(creds, project=PROJECT_ID)
    else:
        # En local (sur ton PC) : on lit le fichier key.json
        return bigquery.Client.from_service_account_json("key.json", project=PROJECT_ID)

# =============================================
# GESTION DES CLIENTS (Clés API)
# =============================================
VALID_API_KEYS = {
    "demo_123456": {"name": "Client Demo", "plan": "Starter"},
}

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=403, detail="Clé API invalide")
    return VALID_API_KEYS[x_api_key]

# =============================================
# ENDPOINTS
# =============================================

@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API des taux de transfert"}

@app.get("/v1/latest")
def get_latest_rates(client_info: dict = Depends(verify_api_key)):
    client = get_bigquery_client()
    
    query = f"""
    SELECT operateur, frais_application, taux_de_change, montant_recu, promo, timestamp_collecte
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    WHERE timestamp_collecte = (
        SELECT MAX(timestamp_collecte) FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    )
    ORDER BY montant_recu DESC
    """
    
    results = client.query(query)
    rows = [dict(row) for row in results]
    
    if not rows:
        raise HTTPException(status_code=404, detail="Aucune donnée")
    
    return {
        "status": "success",
        "client": client_info["name"],
        "plan": client_info["plan"],
        "timestamp": rows[0]["timestamp_collecte"].isoformat(),
        "data": rows
    }

@app.get("/v1/health")
def health_check():
    return {"status": "online"}
