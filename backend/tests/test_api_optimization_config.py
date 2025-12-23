"""Test OptimizationConfig API endpoints."""

import requests
import json

BASE_URL = "http://localhost:8000"

# Login to get token
print("=== Logging in as admin ===")
login_response = requests.post(f"{BASE_URL}/users/login", json={
    "user_email": "admin@example.com",
    "user_password": "admin123"
})
print(f"Login status: {login_response.status_code}")
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Test 1: Create optimization config
print("\n=== Test 1: Create Optimization Config ===")
config_data = {
    "config_name": "Fairness Focused",
    "weight_fairness": 0.5,
    "weight_preferences": 0.3,
    "weight_cost": 0.05,
    "weight_coverage": 0.15,
    "max_runtime_seconds": 600,
    "mip_gap": 0.02,
    "is_default": True
}
response = requests.post(f"{BASE_URL}/optimization-configs/", json=config_data, headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 201:
    config = response.json()
    print(f"Created config ID: {config['config_id']}")
    print(f"Name: {config['config_name']}")
    print(f"Is default: {config['is_default']}")
    config_id = config['config_id']
else:
    print(f"Error: {response.text}")
    exit(1)

# Test 2: Get all configs
print("\n=== Test 2: Get All Configs ===")
response = requests.get(f"{BASE_URL}/optimization-configs/", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    configs = response.json()
    print(f"Total configs: {len(configs)}")
    for cfg in configs:
        print(f"  - {cfg['config_name']} (ID: {cfg['config_id']}, Default: {cfg['is_default']})")
else:
    print(f"Error: {response.text}")

# Test 3: Get default config
print("\n=== Test 3: Get Default Config ===")
response = requests.get(f"{BASE_URL}/optimization-configs/default", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    default_config = response.json()
    print(f"Default config: {default_config['config_name']}")
else:
    print(f"Error: {response.text}")

# Test 4: Get config by ID
print("\n=== Test 4: Get Config by ID ===")
response = requests.get(f"{BASE_URL}/optimization-configs/{config_id}", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    config = response.json()
    print(f"Config name: {config['config_name']}")
    print(f"Weights: F={config['weight_fairness']}, P={config['weight_preferences']}")
else:
    print(f"Error: {response.text}")

# Test 5: Update config
print("\n=== Test 5: Update Config ===")
update_data = {
    "weight_fairness": 0.6,
    "max_runtime_seconds": 900
}
response = requests.put(f"{BASE_URL}/optimization-configs/{config_id}", json=update_data, headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    updated_config = response.json()
    print(f"Updated fairness weight: {updated_config['weight_fairness']}")
    print(f"Updated runtime: {updated_config['max_runtime_seconds']}s")
else:
    print(f"Error: {response.text}")

# Test 6: Create another config
print("\n=== Test 6: Create Another Config (non-default) ===")
config2_data = {
    "config_name": "Preference Focused",
    "weight_fairness": 0.2,
    "weight_preferences": 0.6,
    "weight_cost": 0.05,
    "weight_coverage": 0.15,
    "max_runtime_seconds": 300,
    "mip_gap": 0.01,
    "is_default": False
}
response = requests.post(f"{BASE_URL}/optimization-configs/", json=config2_data, headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 201:
    config2 = response.json()
    print(f"Created config ID: {config2['config_id']}")
    config2_id = config2['config_id']
else:
    print(f"Error: {response.text}")

# Test 7: Try to delete default config (should fail)
print("\n=== Test 7: Try to Delete Default Config (should fail) ===")
response = requests.delete(f"{BASE_URL}/optimization-configs/{config_id}", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 400:
    print(f"✅ Correctly rejected: {response.json()['detail']}")
else:
    print(f"Unexpected result: {response.text}")

# Test 8: Set second config as default
print("\n=== Test 8: Set Second Config as Default ===")
response = requests.put(f"{BASE_URL}/optimization-configs/{config2_id}", json={"is_default": True}, headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ Successfully set as default")
else:
    print(f"Error: {response.text}")

# Test 9: Now delete the first config
print("\n=== Test 9: Delete First Config (now allowed) ===")
response = requests.delete(f"{BASE_URL}/optimization-configs/{config_id}", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ Successfully deleted")
else:
    print(f"Error: {response.text}")

# Test 10: Verify only one config remains
print("\n=== Test 10: Verify Final State ===")
response = requests.get(f"{BASE_URL}/optimization-configs/", headers=headers)
configs = response.json()
print(f"Total configs: {len(configs)}")
for cfg in configs:
    print(f"  - {cfg['config_name']} (Default: {cfg['is_default']})")

print("\n✅ All API tests completed!")
