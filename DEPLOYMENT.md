# PetDigiTwin Agent — Deployment Guide (Path 1: 3-5 Days)

Complete guide to get PetDigiTwin running locally and deployed to Google Cloud Run.

---

## Phase 1: Local Setup (Day 1-2)

### Step 1: Environment Setup

```bash
# Navigate to project
cd /home/esudbat/petdigitwin

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: MongoDB Setup

#### Option A: MongoDB Atlas (Recommended for Cloud Run)

1. Go to https://www.mongodb.com/cloud/atlas
2. Create free account
3. Create a cluster (name: `petdigitwin`)
4. Get connection string (looks like: `mongodb+srv://user:pass@cluster.mongodb.net/petdigitwin`)
5. Create `.env` file:

```bash
cat > .env << 'EOF'
MONGODB_URI=mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@cluster.mongodb.net/petdigitwin?retryWrites=true&w=majority
GOOGLE_API_KEY=your-google-api-key-here
EOF
```

#### Option B: Local MongoDB

```bash
# Install MongoDB (macOS)
brew install mongodb-community

# Start MongoDB
brew services start mongodb-community

# Add to .env
echo "MONGODB_URI=mongodb://localhost:27017/petdigitwin" >> .env
```

### Step 3: Get Google API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable Generative AI API
4. Create API key (or use existing)
5. Add to `.env`:

```bash
echo "GOOGLE_API_KEY=your-key-here" >> .env
```

### Step 4: Initialize Database

```bash
# Load sample data into MongoDB
python3 -c "from src.db import PetDigiTwinDB; db = PetDigiTwinDB(); db.initialize_collections(); db.load_sample_data()"

# Verify data loaded
python3 << 'EOF'
from src.db import PetDigiTwinDB
db = PetDigiTwinDB()
print(f"Pets: {db.db.pets.count_documents({})}")
print(f"Volunteers: {db.db.volunteers.count_documents({})}")
print(f"Foods: {db.db.pet_foods.count_documents({})}")
print(f"Knowledge: {db.db.vet_knowledge.count_documents({})}")
EOF
```

---

## Phase 2: Test Locally (Day 2)

### Option A: Test Agent Directly

```bash
python3 src/agent.py
```

Expected output:
```
======================================================================
USER: Max has been limping for 2 days. What natural remedies can help?
======================================================================
📞 Calling tool: search_health_knowledge with args: {'condition': 'joint_pain'}
📞 Calling tool: find_suitable_food with args: {'pet_id': 'pet_001'}

AGENT: [Response from Gemini about joint pain management...]
```

### Option B: Test API Server

```bash
# Start Flask server
python3 app.py

# In another terminal, test endpoints
curl http://localhost:8080/
curl http://localhost:8080/api/pets
curl http://localhost:8080/api/volunteers

# Test agent query
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What natural remedies help joint pain?", "pet_id": "pet_001"}'
```

---

## Phase 3: Docker Build & Test (Day 3)

### Build Docker Image

```bash
# Build image
docker build -t petdigitwin:latest .

# Test image locally
docker run -p 8080:8080 \
  -e MONGODB_URI="your-mongodb-uri" \
  -e GOOGLE_API_KEY="your-api-key" \
  petdigitwin:latest

# Test from another terminal
curl http://localhost:8080/
```

---

## Phase 4: Deploy to Cloud Run (Day 3-4)

### Prerequisites

```bash
# Install Google Cloud CLI
# https://cloud.google.com/sdk/docs/install

# Login to Google Cloud
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Deploy to Cloud Run

```bash
# Option A: Direct deployment (recommended)
gcloud run deploy petdigitwin \
  --source . \
  --platform managed \
  --region us-central1 \
  --memory 1Gi \
  --cpu 1 \
  --set-secrets MONGODB_URI=MONGODB_URI:latest,GOOGLE_API_KEY=GOOGLE_API_KEY:latest \
  --allow-unauthenticated

# Option B: Push to Artifact Registry first
gcloud builds submit --tag us-central1-docker.pkg.dev/YOUR_PROJECT/cloud-run-source-deploy/petdigitwin

gcloud run deploy petdigitwin \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT/cloud-run-source-deploy/petdigitwin:latest \
  --platform managed \
  --region us-central1 \
  --set-env-vars MONGODB_URI="your-mongodb-uri",GOOGLE_API_KEY="your-api-key"
```

### Verify Deployment

After deployment, you'll get a URL like: `https://petdigitwin-xxx.a.run.app`

```bash
# Test health check
curl https://petdigitwin-xxx.a.run.app/

# Test agent query
curl -X POST https://petdigitwin-xxx.a.run.app/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What natural remedies help joint pain?",
    "pet_id": "pet_001"
  }'
```

---

## Phase 5: Demo & Final Polish (Day 4-5)

### Create Demo Script

```bash
cat > test_agent.sh << 'EOF'
#!/bin/bash

API_URL="https://petdigitwin-xxx.a.run.app"  # Replace with your URL

echo "=== PetDigiTwin Demo ==="
echo ""

echo "1️⃣ Query: Health remedies for limping dog"
curl -s -X POST $API_URL/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Max has been limping. What can I do?", "pet_id": "pet_001"}' | jq .response

echo ""
echo "2️⃣ Query: Find pet sitter for vacation"
curl -s -X POST $API_URL/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "I need a pet sitter for July 1-15", "pet_id": "pet_002"}' | jq .response

echo ""
echo "3️⃣ Query: Food recommendation"
curl -s -X POST $API_URL/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the best food for Charlie?", "pet_id": "pet_003"}' | jq .response
EOF

chmod +x test_agent.sh
./test_agent.sh
```

### Example Queries for Demo Video

```
1. "My dog Max has been limping for 2 days. What can I do?"
2. "I'm planning a vacation July 1-15. Can you help me find a pet sitter for Bella?"
3. "What's the best food for Charlie given he's a senior with arthritis?"
4. "When does Daisy need her next checkup?"
5. "Find volunteers who can care for my Bulldog Frank while I'm away."
```

---

## Troubleshooting

### Issue: MongoDB Connection Error

```bash
# Check MongoDB URI format
# Should be: mongodb+srv://user:pass@cluster.mongodb.net/petdigitwin

# If using local MongoDB, ensure it's running
brew services list | grep mongodb
```

### Issue: Google API Key Error

```bash
# Verify API key in .env
cat .env | grep GOOGLE_API_KEY

# Test with curl
curl -X GET "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents": [{"parts": [{"text": "Hello"}]}]}'
```

### Issue: Cloud Run Deployment Timeout

```bash
# Increase memory
gcloud run update petdigitwin --memory 2Gi

# Increase timeout
gcloud run update petdigitwin --timeout 300s
```

### Issue: Tool Calling Not Working

```bash
# Check tool definitions in src/tools.py
# Ensure function schemas are valid JSON
# Try simpler queries first

# Enable debug logging
export DEBUG=1
python3 app.py
```

---

## Project Structure

```
petdigitwin/
├── app.py                 # Flask API server
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── .env                  # Environment variables (DO NOT COMMIT)
├── DEPLOYMENT.md         # This file
├── src/
│   ├── __init__.py
│   ├── db.py            # MongoDB setup & sample data
│   ├── tools.py         # MCP tools for Gemini
│   └── agent.py         # Main Gemini agent orchestrator
└── config/
    └── .gcloudignore    # (optional)
```

---

## Quick Start Checklist

- [ ] Python 3.11+ installed
- [ ] MongoDB Atlas account created
- [ ] Google API key obtained
- [ ] `.env` file with credentials
- [ ] `pip install -r requirements.txt`
- [ ] Database initialized: `python3 src/agent.py`
- [ ] Local test passed: `python3 app.py` + curl
- [ ] Docker image built and tested
- [ ] Cloud Run deployed
- [ ] Demo queries working

---

## Next Steps (Optional Enhancements)

After the basic 3-5 day MVP is working:

1. **Add Arize** (week 2) — Add observability and LLM-as-Judge evals
2. **Add Fivetran** (week 3) — Auto-sync data from pet wearables
3. **Add more tools** — Weather-based alerts, vet appointment scheduling
4. **Add UI** — Simple web dashboard to query the agent

---

## Support

For issues:
1. Check `.env` variables
2. Verify MongoDB connection
3. Test with simpler queries
4. Check Cloud Run logs: `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=petdigitwin" --limit 50`
5. Review error messages in stderr
