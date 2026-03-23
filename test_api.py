import httpx
import time
import subprocess
import os
import signal

def run_tests():
    base_url = "http://127.0.0.1:8000"
    
    # 1. Add Agent
    print("Testing /agents...")
    agent_data = {
        "name": "DocParser",
        "description": "Extracts structured data from PDFs",
        "endpoint": "https://api.example.com/parse"
    }
    response = httpx.post(f"{base_url}/agents", json=agent_data)
    assert response.status_code == 201
    print("Add Agent success.")

    # 2. List Agents
    response = httpx.get(f"{base_url}/agents")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    print("List Agents success.")

    # 3. Search Agents
    print("Testing /search...")
    response = httpx.get(f"{base_url}/search", params={"q": "pdf"})
    assert response.status_code == 200
    assert any(a["name"] == "DocParser" for a in response.json())
    print("Search Agents success.")

    # 4. Log Usage
    print("Testing /usage...")
    usage_data = {
        "caller": "AgentA",
        "target": "DocParser",
        "units": 10,
        "request_id": "abc123"
    }
    response = httpx.post(f"{base_url}/usage", json=usage_data)
    assert response.status_code == 200
    assert response.json()["status"] == "recorded"
    
    # Test Idempotency (Duplicate request_id)
    response = httpx.post(f"{base_url}/usage", json=usage_data)
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    print("Usage Logging and Idempotency success.")

    # 5. Usage Summary
    print("Testing /usage-summary...")
    response = httpx.get(f"{base_url}/usage-summary")
    assert response.status_code == 200
    assert response.json()["DocParser"] == 10
    print("Usage Summary success.")

    # 6. Edge Case: Unknown agent
    print("Testing unknown agent usage...")
    bad_usage = {
        "caller": "AgentA",
        "target": "UnknownAgent",
        "units": 10,
        "request_id": "xyz789"
    }
    response = httpx.post(f"{base_url}/usage", json=bad_usage)
    assert response.status_code == 404
    print("Unknown agent error handling success.")

    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    # Note: This script assumes the server is already running.
    try:
        run_tests()
    except Exception as e:
        import traceback
        print(f"Test failed: {e}")
        traceback.print_exc()
