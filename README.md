# PetDigiTwin — AI Agent for Pet Health & Care

A Google Gemini-powered agent that provides one-stop pet health solutions: daily health monitoring, nutrition tracking, natural recovery suggestions, proactive checkup alerts, and pet sitter matching for vacation planning.

## ✨ Features

- **Health Monitoring** — Daily pet health tracking with anomaly detection
- **Nutrition Guidance** — Personalized food recommendations based on pet conditions
- **Natural Recovery** — Suggest natural remedies for common pet ailments
- **Proactive Checkups** — Predict when pets need veterinary care
- **Volunteer Matching** — Find trusted pet sitters for vacation planning
- **Knowledge Base** — RAG over veterinary information and natural remedies

## 🚀 Quick Start (3-5 Days)

### Prerequisites

- Python 3.11+
- MongoDB Atlas account (free tier)
- Google API key for Gemini
- Google Cloud account (for Cloud Run)

### Local Setup

```bash
# 1. Clone and setup
git clone <repo>
cd petdigitwin
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your MongoDB URI and Google API key

# 3. Initialize database
python3 -c "from src.db import PetDigiTwinDB; db = PetDigiTwinDB(); db.initialize_collections(); db.load_sample_data()"

# 4. Test agent locally
python3 src/agent.py

# 5. Run API server
python3 app.py
# Visit http://localhost:8080/
```

### Deploy to Cloud Run

```bash
# Build and deploy (one command)
gcloud run deploy petdigitwin \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars MONGODB_URI="<uri>",GOOGLE_API_KEY="<key>" \
  --allow-unauthenticated
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

---

## 📋 Architecture

```
User Query
    ↓
Gemini Agent (Google Gemini 2.0 Flash)
    ↓ (calls tools)
MCP Tools:
  ├─ search_health_knowledge (RAG over vet docs)
  ├─ find_suitable_food (nutrition search)
  ├─ predict_checkup_need (health proactive)
  ├─ find_volunteers_for_pet (pet sitter matching)
  └─ get_pet_health_summary (profile overview)
    ↓
MongoDB Atlas (data store)
    ├─ Pets
    ├─ Volunteers
    ├─ Pet Foods
    └─ Vet Knowledge Base
    ↓
Response to User
```

---

## 🛠 Tech Stack (Path 1)

| Component | Technology | Why |
|---|---|---|
| **Agent Runtime** | Google Gemini SDK | Required for hackathon |
| **Data Store** | MongoDB Atlas | Simpler JSON model vs Elasticsearch |
| **Tools** | MCP (Model Context Protocol) | Function calling + tool exposure |
| **Deployment** | Google Cloud Run | Serverless, scales automatically |
| **API** | Flask | Lightweight, fast to setup |

---

## 📁 Project Structure

```
petdigitwin/
├── app.py                      # Flask API server
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container config
├── .env.example               # Environment template
├── DEPLOYMENT.md              # Full deployment guide
├── README.md                  # This file
└── src/
    ├── __init__.py
    ├── db.py                  # MongoDB: collections + sample data (10 pets, 5 volunteers, etc.)
    ├── tools.py               # 5 MCP tools for Gemini agent
    └── agent.py               # Main agent orchestrator (tool calling loop)
```

---

## 🎯 Sample Queries

```bash
# 1. Health remedy
"Max has been limping for 2 days. What natural remedies can help?"

# 2. Pet sitter search
"I'm going on vacation July 1-15. Find a pet sitter for Bella."

# 3. Food recommendation
"What's the best food for Charlie given his arthritis and diabetes?"

# 4. Checkup prediction
"Tell me about Daisy's health and when she needs her next checkup."

# 5. Volunteer matching
"Find volunteers experienced with Bulldogs for emergency pet care."
```

---

## API Endpoints

### Health Check
```bash
GET /
```

### Agent Query
```bash
POST /api/query
Content-Type: application/json

{
  "query": "What remedies help with joint pain?",
  "pet_id": "pet_001",           # optional
  "max_iterations": 5            # optional
}
```

### Data Lookups
```bash
GET /api/pets                 # List all pets
GET /api/pets/{id}            # Get pet details
GET /api/volunteers           # List volunteers
GET /api/foods                # List foods
GET /api/knowledge            # List vet knowledge
```

---

## ⏱ Timeline (3-5 Days)

### Day 1: Setup
- [ ] Project structure created
- [ ] MongoDB configured (1-2 hours)
- [ ] Google API key obtained (30 min)
- [ ] Database schema defined (1 hour)
- [ ] Sample data loaded (1 hour)

### Day 2: Agent Development
- [ ] MCP tools implemented (2-3 hours)
- [ ] Gemini agent orchestrator built (2-3 hours)
- [ ] Tool calling loop tested locally (1 hour)

### Day 3: API & Deployment
- [ ] Flask API server created (1-2 hours)
- [ ] Docker image built (1 hour)
- [ ] Cloud Run deployment (1-2 hours)

### Day 4-5: Polish & Demo
- [ ] Final testing
- [ ] Create demo script
- [ ] Record demo video (3 min)
- [ ] Buffer for fixes

---

## 🚫 What's NOT Included (Add Later)

These are in the **Path 1 skip list**:

- **Arize** — Skipped for MVP (add week 2 for eval+observability)
- **Fivetran** — Skipped for MVP (add week 3 for auto data syncing)
- **Agent Runtime** — Using Cloud Run instead (simpler)
- **UI Dashboard** — API-only for MVP

---

## 🔧 Troubleshooting

### MongoDB Connection Error
```bash
# Check URI format and ensure MongoDB Atlas is accepting connections
# Whitelist your IP in MongoDB Atlas
```

### Google API Key Error
```bash
# Verify key has Generative AI API enabled
# Check key is not rate-limited
```

### Tool Calling Fails
```bash
# Ensure tool schemas match Gemini's expectations
# Try simpler queries first
# Check MongoDB has sample data
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for more.

---

## 📖 Next Steps

**After MVP (weeks 2-3):**

1. Add Arize Phoenix for observability + evaluations
2. Add Fivetran for real-time pet wearable data
3. Add more tools (vet scheduling, emergency alerts)
4. Build simple web UI for pet owners
5. Add user authentication + multi-pet support

---

## 📝 License

MIT

---

## 👥 Support

For issues, see [DEPLOYMENT.md](DEPLOYMENT.md) troubleshooting section.

---

## 🎯 For Hackathon Judges

**Why this matters:**
- ✅ **Production-ready** — Deployed on Cloud Run, scales automatically
- ✅ **Real tools** — 5 functional MCP tools called by Gemini agent
- ✅ **Real data** — 10 sample pets, 5 volunteers, nutrition DB, vet knowledge
- ✅ **Fast to MVP** — 3-5 days to working demo
- ✅ **Health-focused** — Helps owners make data-driven pet care decisions
- ✅ **Extensible** — Easy to add real APIs (Fitbit, vet clinic systems, etc.)

**Demo:** Query agent with pet-specific questions → Get personalized recommendations → See tool calls in action.
# petdigitwin
