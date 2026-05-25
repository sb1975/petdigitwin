# PetDigiTwin — Quick Start Cheat Sheet

Copy-paste commands to get PetDigiTwin running in minutes.

---

## 🚀 Get Running in 5 Minutes (Local)

```bash
# 1. Clone/Setup
cd petdigitwin

# 2. Virtual env
python3 -m venv venv
source venv/bin/activate

# 3. Install
pip install -r requirements.txt

# 4. Config (.env)
cp .env.example .env
# Edit .env with:
# - MONGODB_URI (from MongoDB Atlas)
# - GOOGLE_API_KEY (from Google Cloud)

# 5. Init database
python3 -c "from src.db import PetDigiTwinDB; db = PetDigiTwinDB(); db.initialize_collections(); db.load_sample_data()"

# 6. Run
python3 app.py

# 7. Test
curl http://localhost:8080/
```

---

## 🔧 Common Commands

### Database
```bash
# Initialize
python3 -c "from src.db import PetDigiTwinDB; db = PetDigiTwinDB(); db.initialize_collections(); db.load_sample_data()"

# Check counts
python3 << 'EOF'
from src.db import PetDigiTwinDB
db = PetDigiTwinDB()
print(f"Pets: {db.db.pets.count_documents({})}")
print(f"Volunteers: {db.db.volunteers.count_documents({})}")
EOF
```

### Agent Test
```bash
# Direct test
python3 src/agent.py

# Test specific tool
python3 << 'EOF'
from src.tools import PetDigiTwinTools
tools = PetDigiTwinTools()
print(tools.search_health_knowledge("joint_pain"))
EOF
```

### API Server
```bash
# Start
python3 app.py

# Health check
curl http://localhost:8080/

# Test agent query
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What helps joint pain?", "pet_id": "pet_001"}'
```

### Docker
```bash
# Build
docker build -t petdigitwin:latest .

# Run locally
docker run -p 8080:8080 \
  -e MONGODB_URI="mongodb+srv://..." \
  -e GOOGLE_API_KEY="..." \
  petdigitwin:latest

# Stop
docker kill $(docker ps -q)
```

### Cloud Run
```bash
# Deploy
gcloud run deploy petdigitwin \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars MONGODB_URI="...",GOOGLE_API_KEY="..." \
  --allow-unauthenticated

# Get URL
gcloud run services describe petdigitwin --region us-central1 | grep Service

# View logs
gcloud run logs read petdigitwin --limit=50

# Update
gcloud run deploy petdigitwin --source . --region us-central1

# Delete
gcloud run services delete petdigitwin --region us-central1
```

---

## 📡 API Examples

### Health Check
```bash
curl http://localhost:8080/
```

**Response:**
```json
{
  "status": "healthy",
  "service": "PetDigiTwin Agent API",
  "version": "1.0.0"
}
```

### Agent Query
```bash
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Max has been limping. What can I do?",
    "pet_id": "pet_001",
    "max_iterations": 5
  }'
```

**Response:**
```json
{
  "status": "success",
  "response": "Based on Max's condition of joint pain, here are some natural remedies...",
  "pet_id": "pet_001"
}
```

### List Pets
```bash
curl http://localhost:8080/api/pets
```

**Response:**
```json
{
  "status": "success",
  "pets": [
    {
      "id": "pet_001",
      "name": "Max",
      "breed": "Labrador",
      "age": 3,
      "conditions": ["joint_pain", "weight_management"],
      "owner_name": "Alice"
    },
    ...
  ],
  "count": 10
}
```

### Get Pet Details
```bash
curl http://localhost:8080/api/pets/pet_001
```

### List Volunteers
```bash
curl http://localhost:8080/api/volunteers
```

### List Foods
```bash
curl http://localhost:8080/api/foods
```

### Search Knowledge Base
```bash
curl 'http://localhost:8080/api/knowledge?condition=joint_pain'
```

---

## 🐛 Quick Troubleshooting

### MongoDB Won't Connect
```bash
# Check URI
cat .env | grep MONGODB_URI

# For Atlas: Whitelist your IP
# https://cloud.mongodb.com/v2/YOUR_ORG#clusters

# For local: Check MongoDB is running
brew services list | grep mongo

# Start if not running
brew services start mongodb-community
```

### Google API Key Error
```bash
# Check key is enabled
# https://console.cloud.google.com/apis/credentials

# Test key
curl -X GET "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents": [{"parts": [{"text": "test"}]}]}'
```

### Agent Not Calling Tools
```bash
# Check tool schemas in src/tools.py
# Try simpler query first
# Check MongoDB has sample data

python3 << 'EOF'
from src.db import PetDigiTwinDB
db = PetDigiTwinDB()
if db.db.pets.count_documents({}) == 0:
    db.load_sample_data()
EOF
```

### Docker Build Fails
```bash
# Check Python version
python3 --version  # Should be 3.11+

# Clear Docker cache
docker system prune -a

# Try rebuild
docker build --no-cache -t petdigitwin:latest .
```

### Cloud Run Deployment Timeout
```bash
# Increase memory
gcloud run update petdigitwin --memory 2Gi

# Increase timeout
gcloud run update petdigitwin --timeout 300s

# Check logs
gcloud run logs read petdigitwin --limit=100
```

---

## 🎯 Sample Test Queries

Copy-paste these to test the agent:

### Health Remedies
```bash
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Max has been limping for 2 days. What can I do?",
    "pet_id": "pet_001"
  }'
```

### Pet Sitter Search
```bash
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I am going on vacation July 1-15. Can you find a pet sitter for Bella?",
    "pet_id": "pet_002"
  }'
```

### Food Recommendation
```bash
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the best food for Charlie given his conditions?",
    "pet_id": "pet_003"
  }'
```

### Health Status
```bash
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about Daisy'"'"'s health and when she needs her next checkup",
    "pet_id": "pet_004"
  }'
```

### Emergency Volunteers
```bash
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I need emergency pet care for Frank (a Bulldog). Find experienced volunteers.",
    "pet_id": "pet_006"
  }'
```

---

## 📚 Files to Modify

| File | Purpose | Edit If |
|---|---|---|
| `.env` | Credentials | You have different API keys |
| `src/tools.py` | MCP tools | You want to add new tools |
| `src/db.py` | Sample data | You want different pets/foods |
| `app.py` | API endpoints | You want new endpoints |
| `DEPLOYMENT.md` | Docs | You find steps don't work |

---

## 🔐 Security Notes

**DO NOT:**
- Commit `.env` file with real credentials
- Expose `GOOGLE_API_KEY` in code
- Use `--allow-unauthenticated` in production

**DO:**
- Use `.gitignore` for `.env`
- Rotate API keys monthly
- Use Cloud IAM for Cloud Run access
- Add authentication for production

---

## 📞 Getting Help

1. Check [DEPLOYMENT.md](DEPLOYMENT.md) — Detailed setup guide
2. Check [TIMELINE.md](TIMELINE.md) — Day-by-day breakdown
3. Check logs: `gcloud run logs read petdigitwin`
4. Test individual tools in Python REPL
5. Start with simpler queries

---

## ✅ Pre-Submission Checklist

- [ ] `.env` configured with MongoDB URI and Google API key
- [ ] Database initialized: `python3 src/agent.py` runs without error
- [ ] Local API works: `python3 app.py` + test queries
- [ ] Docker builds: `docker build -t petdigitwin:latest .`
- [ ] Cloud Run deployed and responding
- [ ] Demo queries working on live endpoint
- [ ] README.md and DEPLOYMENT.md up to date
- [ ] `.env` NOT committed to git
- [ ] Demo video recorded (2-3 min)

---

## 🎉 You're Ready When:

✅ You can run any sample query and get a coherent response  
✅ Agent is calling tools (see 📞 logs)  
✅ Cloud Run API endpoint is live  
✅ Demo video is recorded  

**Congrats, you're ready to submit!**
