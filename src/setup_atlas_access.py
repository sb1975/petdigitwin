import os
import requests
from requests.auth import HTTPDigestAuth
from dotenv import load_dotenv

load_dotenv()

def get_public_ip():
    """Fetches the public IP address of the current environment."""
    try:
        response = requests.get("https://api.ipify.org", timeout=5)
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Warning: Could not auto-detect public IP: {e}")
        return None

def whitelist_ips(ip_address=None, comment=None):
    """
    Automates adding an IP address to MongoDB Atlas IP Access List via API.
    Requires ATLAS_PUBLIC_KEY, ATLAS_PRIVATE_KEY, and ATLAS_PROJECT_ID in .env.
    """

    public_key = os.getenv("ATLAS_PUBLIC_KEY")
    private_key = os.getenv("ATLAS_PRIVATE_KEY")
    project_id = os.getenv("ATLAS_PROJECT_ID")

    if not all([public_key, private_key, project_id]):
        print("❌ Error: ATLAS_PUBLIC_KEY, ATLAS_PRIVATE_KEY, and ATLAS_PROJECT_ID must be set in .env")
        print("Find these in your MongoDB Atlas Project Settings -> API Keys (Digest Auth).")
        return

    if not ip_address:
        detected_ip = get_public_ip()
        if not detected_ip:
            print("❌ Error: Could not determine public IP and no IP provided.")
            return
        ip_address = f"{detected_ip}/32"
        comment = comment or f"Auto-detected Container IP - {detected_ip}"

    comment = comment or "Hackathon - Cloud Run Access"
    url = f"https://cloud.mongodb.com/api/atlas/v1.0/groups/{project_id}/accessList"
    
    # Payload format for Atlas API
    data = [
        {
            "ipAddress": ip_address,
            "comment": comment
        }
    ]

    try:
        response = requests.post(
            url,
            auth=HTTPDigestAuth(public_key, private_key),
            json=data,
            timeout=10
        )
        if response.status_code in [200, 201]:
            print(f"✅ Successfully whitelisted {ip_address} in MongoDB Atlas.")
        elif response.status_code == 409:
            print(f"ℹ️  {ip_address} is already whitelisted.")
        elif response.status_code == 401:
            print("❌ Failed to update Atlas: 401 Unauthorized")
            print("💡 Tip: Ensure your ATLAS_PUBLIC_KEY and ATLAS_PRIVATE_KEY are correct.")
            print("💡 Tip: You MUST add your current IP to the 'API Key IP Access List' in the Atlas UI.")
            print(f"   Response: {response.text}")
        else:
            print(f"❌ Failed to update Atlas: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    whitelist_ips()