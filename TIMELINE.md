# PetDigiTwin — Day-by-Day Development Timeline (Path 1)

Complete breakdown of how to build, test, and deploy PetDigiTwin in 3-5 days.

---

## 📅 Day 1: Environment & Database Setup (3-4 hours)

### Morning (1.5 hours)

**Goal:** Get development environment ready

```bash
# 1. Create project directory
mkdir petdigitwin && cd petdigitwin

# 2. Initialize git (optional)
git init

# 3. Create Python venv
python3 -m venv venv
source venv/bin/activate

# 4. Install initial dependencies
pip install google-genai pymongo flask python-dotenv

# 5. Create folder structure
mkdir -p src config data
touch src/__init__.py

# Time check: 30 min
```

### Late Morning (1 hour)

**Goal:** Set up MongoDB

**Option A: Cloud (Recommended)**
1. Go to https://mongodb.com/cloud/atlas
2. Create free account (5 min)
3. Create cluster named `petdigitwin` (10 min)
4. Get connection string (5 min)
5. Create `.env` file (5 min):

```bash
cat > .env << 'EOF'
MONGODB_URI=mongodb+srv://your-username:your-password@cluster.mongodb.net/petdigitwin?retryWrites=true&w=majority
GOOGLE_API_KEY=PENDING  # Will fill in later
EOF
```

**Option B: Local**
```bash
brew install mongodb-community
brew services start mongodb-community
echo "MONGODB_URI=mongodb://localhost:27017/petdigitwin" >> .env
```

### Afternoon (1-1.5 hours)

**Goal:** Create database schema and load sample data

1. Create [src/db.py](src/db.py) — Database initialization script
2. Run database setup:

```bash
python3 -c "from src.db import PetDigiTwinDB; db = PetDigiTwinDB(); db.initialize_collections(); db.load_sample_data()"
```

3. Verify:

```bash
python3 << 'EOF'
from src.db import PetDigiTwinDB
db = PetDigiTwinDB()
print(f"✅ Pets: {db.db.pets.count_documents({})}")
print(f"✅ Volunteers: {db.db.volunteers.count_documents({})}")
print(f"✅ Foods: {db.db.pet_foods.count_documents({})}")
print(f"✅ Knowledge: {db.db.vet_knowledge.count_documents({})}")
EOF
```

**Expected output:**
```
✅ Pets: 10
✅ Volunteers: 5
✅ Foods: 8
✅ Knowledge: 6
```

**End of Day 1 Checklist:**
- ✅ Python venv set up
- ✅ MongoDB running and accessible
- ✅ `.env` file created
- ✅ Database initialized with 10 pets, 5 volunteers, 8 foods, 6 vet knowledge entries

---

## 📅 Day 2: Gemini Agent & Tools (4-5 hours)

### Morning (2-2.5 hours)

**Goal:** Create MCP tools that Gemini will call

1. Create [src/tools.py](src/tools.py)
   - 5 tools: health search, food finder, checkup predictor, volunteer matcher, health summary
   - Each tool queries MongoDB and returns structured JSON

2. Test tools independently:

```bash
python3 << 'EOF'
from src.tools import PetDigiTwinTools

tools = PetDigiTwinTools()

# Test tool 1: Search health knowledge
result = tools.search_health_knowledge("joint_pain")
print("Health Knowledge Search:", result)

# Test tool 2: Find suitable food
result = tools.find_suitable_food("pet_001", condition="weight_management")
print("Food Recommendation:", result)

# Test tool 3: Predict checkup need
result = tools.predict_checkup_need("pet_001")
print("Checkup Prediction:", result)
EOF
```

### Late Morning (1.5-2 hours)

**Goal:** Create Gemini agent with tool calling

1. Get Google API key:
   - Go to https://console.cloud.google.com
   - Enable Generative AI API
   - Create API key
   - Add to `.env`:
   ```bash
   echo "GOOGLE_API_KEY=your-key-here" >> .env
   ```

2. Create [src/agent.py](src/agent.py)
   - Initialize Gemini model with tools
   - Implement agent loop (question → tool call → answer)
   - Handle function calling from Gemini

### Afternoon (1-1.5 hours)

**Goal:** Test agent locally

```bash
# Run agent test
python3 src/agent.py
```

**Expected output:**
```
======================================================================
USER: Max has been limping for 2 days. What natural remedies can help?
======================================================================
📞 Calling tool: search_health_knowledge with args: {'condition': 'joint_pain'}
📞 Calling tool: find_suitable_food with args: {'pet_id': 'pet_001'}

AGENT: Based on Max's condition, here are the natural remedies...
```

**End of Day 2 Checklist:**
- ✅ 5 MCP tools implemented and tested
- ✅ Google API key obtained
- ✅ Gemini agent orchestrator working
- ✅ Agent successfully calls tools and synthesizes responses
- ✅ Test with 3-4 sample queries working

---

## 📅 Day 3: API & Docker Deployment (4-5 hours)

### Morning (2 hours)

**Goal:** Build Flask API server

1. Create [app.py](app.py)
   - `GET /` — health check
   - `POST /api/query` — main agent query endpoint
   - `GET /api/pets` — list pets
   - `GET /api/pets/{id}` — get pet details
   - `GET /api/volunteers` — list volunteers
   - Additional data endpoints

2. Test Flask locally:

```bash
python3 app.py
# Visit http://localhost:8080/
```

### Late Morning (1.5-2 hours)

**Goal:** Build and test Docker image

1. Create [Dockerfile](Dockerfile)
2. Create [.dockerignore](.dockerignore)
3. Build and test:

```bash
# Build
docker build -t petdigitwin:latest .

# Test
docker run -p 8080:8080 \
  -e MONGODB_URI="your-mongodb-uri" \
  -e GOOGLE_API_KEY="your-api-key" \
  petdigitwin:latest

# In another terminal
curl http://localhost:8080/
```

### Afternoon (1-1.5 hours)

**Goal:** Deploy to Cloud Run

```bash
# Deploy (one command)
gcloud run deploy petdigitwin \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars MONGODB_URI="your-mongodb-uri",GOOGLE_API_KEY="your-api-key" \
  --allow-unauthenticated

# Get the service URL
gcloud run services describe petdigitwin --region us-central1
```

**Expected output:**
```
Service URL: https://petdigitwin-xxx.a.run.app
```

Test live deployment:
```bash
curl https://petdigitwin-xxx.a.run.app/
curl https://petdigitwin-xxx.a.run.app/api/pets
```

**End of Day 3 Checklist:**
- ✅ Flask API server created
- ✅ All endpoints tested locally
- ✅ Docker image builds successfully
- ✅ Cloud Run deployment successful
- ✅ Live API endpoints responding

---

## 📅 Day 4-5: Polish & Demo (Variable)

### Day 4 (2-3 hours)

**Goal:** Testing and refinement

```bash
# Run comprehensive test suite
cat > test_suite.sh << 'EOF'
#!/bin/bash
API_URL="https://petdigitwin-xxx.a.run.app"

echo "Test 1: Health Check"
curl -s $API_URL/ | jq .

echo "Test 2: List Pets"
curl -s $API_URL/api/pets | jq .

echo "Test 3: Query - Joint Pain Remedy"
curl -s -X POST $API_URL/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What helps joint pain?", "pet_id": "pet_001"}' | jq .response

echo "Test 4: Query - Pet Sitter"
curl -s -X POST $API_URL/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Find a pet sitter", "pet_id": "pet_002", "start_date": "2026-07-01", "end_date": "2026-07-15"}' | jq .response
EOF

chmod +x test_suite.sh
./test_suite.sh
```

### Day 5 (2-3 hours)

**Goal:** Create demo

Create demo video script:
```
Scene 1: "Pet Owner's Challenge"
- Show the problem: Too many health concerns, hard to track

Scene 2: "Introduce PetDigiTwin"
- Query 1: "Max has been limping. What can I do?"
- Show agent response with tools being called

Scene 3: "Vacation Planning"
- Query 2: "I need a pet sitter for Bella"
- Show volunteer recommendations

Scene 4: "Proactive Health"
- Query 3: "Tell me about Charlie's health status"
- Show checkup prediction

Scene 5: "Call to Action"
- "PetDigiTwin: One app for all your pet needs"
```

**Record with:**
```bash
# Simple screen recording (macOS)
screencapture -T 5 -x demo.mov

# Or use OBS for professional recording
# https://obsproject.com/
```

**End of Day 4-5:**
- ✅ All endpoints tested
- ✅ Demo video recorded (2-3 min)
- ✅ Documentation complete
- ✅ Ready for submission

---

## ⏱ Time Breakdown

| Phase | Time | Notes |
|---|---|---|
| **Day 1: Setup** | 3-4 hrs | MongoDB + DB schema |
| **Day 2: Agent** | 4-5 hrs | Tools + Gemini integration |
| **Day 3: Deploy** | 4-5 hrs | API + Docker + Cloud Run |
| **Day 4-5: Polish** | 4-6 hrs | Testing + demo video |
| **TOTAL** | 15-20 hrs | Over 3-5 calendar days |

---

## 🎯 Key Milestones

### Day 1 End
- [ ] Database with 10 sample pets

### Day 2 End
- [ ] Agent successfully calling 5 tools
- [ ] Tool responses integrated into final answer

### Day 3 End
- [ ] Live API on Cloud Run
- [ ] All endpoints responding
- [ ] Sample queries working

### Day 4-5 End
- [ ] Comprehensive testing complete
- [ ] Demo video recorded
- [ ] Ready for submission

---

## 🚀 Quick Commands Reference

### Setup
```bash
cd petdigitwin
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Database
```bash
python3 -c "from src.db import PetDigiTwinDB; db = PetDigiTwinDB(); db.initialize_collections(); db.load_sample_data()"
```

### Local Test
```bash
python3 app.py
# Visit http://localhost:8080/
```

### Docker Test
```bash
docker build -t petdigitwin:latest .
docker run -p 8080:8080 -e MONGODB_URI="uri" -e GOOGLE_API_KEY="key" petdigitwin:latest
```

### Deploy
```bash
gcloud run deploy petdigitwin --source . --platform managed --region us-central1 --set-env-vars MONGODB_URI="uri",GOOGLE_API_KEY="key" --allow-unauthenticated
```

---

## 📝 Notes

- **MongoDB Atlas** free tier supports ~512MB — plenty for this MVP
- **Google API** has generous free tier for Gemini
- **Cloud Run** free tier: 2M requests/month — should be enough for hackathon
- **Total cost for MVP:** ~$0-10 if you stay within free tiers

---

## 🤔 If You Get Stuck

**Day 1 stuck?** → Check MongoDB connection string, verify credentials
**Day 2 stuck?** → Start with simpler query, test each tool individually
**Day 3 stuck?** → Try `gcloud run logs read petdigitwin` to see errors
**Day 4 stuck?** → Record simpler demo, focus on one feature

---

## ✨ Success Indicators

- ✅ Agent answers coherent pet health questions
- ✅ Tools are actually called (see 📞 logs)
- ✅ API responds in < 5 seconds
- ✅ Cloud Run deployment is live and stable
- ✅ Demo shows tool calling in action

**You're ready to submit when all of the above are working!**
