import sys
import os
import requests
import math

# Add backend to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import SavingProduct

# Example: https://winsurdf-backend.onrender.com
REMOTE_BASE_URL = os.getenv("REMOTE_BASE_URL")

BATCH_SIZE = 100

def main():
    if not REMOTE_BASE_URL:
        print("Error: REMOTE_BASE_URL environment variable is not set.")
        print("Please set it like: $env:REMOTE_BASE_URL='https://your-app.onrender.com'")
        return

    # Remove trailing slash
    base_url = REMOTE_BASE_URL.rstrip("/")
    api_url = f"{base_url}/api/v1/admin/sync-market-products"

    print(f"Connecting to local DB to fetch products...")
    db = SessionLocal()
    try:
        products = db.query(SavingProduct).all()
        print(f"Found {len(products)} saving products locally.")
        
        if not products:
            print("No products to sync.")
            return

        payloads = []
        for p in products:
            # Skip invalid products
            if not p.fund_code or not p.fund_name:
                continue
                
            payloads.append({
                "fundType": p.fund_type or "כללי",
                "companyName": p.company_name or "לא ידוע",
                "fundName": p.fund_name,
                "fundCode": p.fund_code,
                "yield1yr": p.yield_1yr,
                "yield3yr": p.yield_3yr,
                "riskLevel": p.risk_level,
                "guaranteedReturn": p.guaranteed_return,
            })

        print(f"Prepared {len(payloads)} valid payloads.")
        total_batches = math.ceil(len(payloads) / BATCH_SIZE)
        
        for i in range(total_batches):
            batch = payloads[i * BATCH_SIZE : (i + 1) * BATCH_SIZE]
            print(f"Sending batch {i+1}/{total_batches} ({len(batch)} items) to {api_url}...")
            
            try:
                resp = requests.post(api_url, json=batch, timeout=60)
                resp.raise_for_status()
                print(f"  -> Success: {resp.json()}")
            except Exception as e:
                print(f"  -> Error: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"     Response: {e.response.text}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
