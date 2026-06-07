import os
import google.auth
from google.cloud import secretmanager
from google.api_core import exceptions
from dotenv import dotenv_values

def create_secrets_from_env(env_path=".env", project_id=None):
    """
    Reads a .env file and creates/updates secrets in Google Cloud Secret Manager.
    """
    if not os.path.exists(env_path):
        print(f"❌ Error: {env_path} file not found.")
        return

    if not project_id:
        # Get the current Google Cloud project ID using application default credentials
        try:
            _, project_id = google.auth.default()
            if not project_id:
                raise ValueError("Project ID not found in environment.")
        except Exception as e:
            print(f"❌ Error: Could not determine project ID. {e}")
            return

    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{project_id}"
    
    # Load keys and values from .env
    config = dotenv_values(env_path)
    
    for key, value in config.items():
        if not value:
            continue
            
        secret_id = key
        # Create the secret if it doesn't already exist
        try:
            client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {"replication": {"automatic": {}}},
                }
            )
            print(f"✅ Created secret: {secret_id}")
        except exceptions.AlreadyExists:
            print(f"ℹ️ Secret {secret_id} already exists.")

        # Add a new secret version
        client.add_secret_version(
            request={
                "parent": f"{parent}/secrets/{secret_id}",
                "payload": {"data": value.encode("UTF-8")},
            }
        )
        print(f"🚀 Added new version to secret: {secret_id}")

if __name__ == "__main__":
    create_secrets_from_env()