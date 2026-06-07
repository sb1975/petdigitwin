"""
PetDigiTwin Flask API Server
Ready for deployment to Google Cloud Run
"""
import os
import json
import time
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
from opentelemetry import trace
from src.agent import PetDigiTwinAgent
from src.db import PetDigiTwinDB
from src.observability import setup_observability, get_observability_status
from src.setup_atlas_access import whitelist_ips
from src.ui import MAIN_PAGE

load_dotenv()
OBSERVABILITY_STATE = setup_observability()
TRACER = trace.get_tracer("petdigitwin.app")

app = Flask(__name__)

# Initialize on startup
agent = None
db = None

def startup_initialization():
    """Ensures the environment is ready (IP whitelisting, DB connection) at container spin-up."""
    global agent, db
    
    # 1. Whitelist the container's outbound IP in MongoDB Atlas
    # This happens once when the container process starts.
    if os.getenv("K_SERVICE"):
        try:
            print("🌐 Cloud Run spin-up detected. Whitelisting container IP in Atlas...")
            whitelist_ips()
        except Exception as e:
            print(f"⚠️  Atlas auto-whitelisting failed: {e}")

    # 2. Initialize Agent and DB
    # The DB connection includes a retry loop to wait for Atlas firewall propagation.
    agent = PetDigiTwinAgent()
    db = PetDigiTwinDB()
    db.initialize_collections()
    
    if db.db.pets.count_documents({}) == 0:
        db.load_sample_data()

# Trigger initialization immediately on container start
startup_initialization()

@app.route("/", methods=["GET"])
def main_ui():
    """Serve the full PetDigiTwin single-page UI."""
    return render_template_string(MAIN_PAGE)

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Cloud Run probes."""
    obs = get_observability_status()
    return jsonify({
        "status": "healthy",
        "service": "PetDigiTwin Agent API",
        "version": "1.0.0",
        "observability": {
            "enabled": obs.get("enabled", False),
            "instrumentors": obs.get("instrumentors", []),
        },
    })

@app.route("/web", methods=["GET"])
def web_test_page():
        """Simple web UI for testing agent queries in a browser."""
        return render_template_string("""
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>PetDigiTwin Web Tester</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; background: #f6f8fb; color: #1f2937; }
        .wrap { max-width: 900px; margin: 30px auto; background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 4px 18px rgba(0,0,0,0.08); }
        h1 { margin-top: 0; font-size: 24px; }
        .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        label { font-size: 14px; font-weight: 600; display: block; margin-bottom: 6px; }
        input, select, textarea { width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; box-sizing: border-box; }
        textarea { min-height: 110px; resize: vertical; }
        button { margin-top: 12px; background: #2563eb; color: #fff; border: none; padding: 10px 16px; border-radius: 8px; cursor: pointer; font-weight: 600; }
        button:disabled { background: #93c5fd; cursor: not-allowed; }
        .panel { margin-top: 16px; }
        pre { background: #0b1020; color: #d1e7ff; padding: 14px; border-radius: 8px; white-space: pre-wrap; overflow-wrap: anywhere; }
        .muted { color: #6b7280; font-size: 13px; }
    </style>
</head>
<body>
    <div class="wrap">
        <h1>PetDigiTwin Web Tester</h1>
        <p class="muted">Use this page to test the same <code>/api/query</code> endpoint from your browser.</p>

        <div class="row">
            <div>
                <label for="pet">Pet</label>
                <select id="pet"></select>
            </div>
            <div>
                <label for="iterations">Max Iterations</label>
                <input id="iterations" type="number" value="5" min="1" max="10" />
            </div>
        </div>

        <div class="panel">
            <label for="query">Question</label>
            <textarea id="query" placeholder="Example: Max has been limping. What should I do naturally?"></textarea>
            <button id="askBtn">Ask PetDigiTwin</button>
        </div>

        <div class="panel">
            <label>Response</label>
            <pre id="output">Waiting for your question...</pre>
        </div>
    </div>

    <script>
        const petSelect = document.getElementById('pet');
        const askBtn = document.getElementById('askBtn');
        const queryEl = document.getElementById('query');
        const output = document.getElementById('output');
        const iterationsEl = document.getElementById('iterations');

        async function loadPets() {
            const res = await fetch('/api/pets');
            const data = await res.json();
            if (!data.pets) {
                output.textContent = 'Failed to load pets';
                return;
            }
            petSelect.innerHTML = data.pets
                .map(p => `<option value="${p.id}">${p.name} (${p.id}) - ${p.breed}</option>`)
                .join('');
        }

        askBtn.addEventListener('click', async () => {
            const query = queryEl.value.trim();
            if (!query) {
                output.textContent = 'Please enter a question first.';
                return;
            }

            askBtn.disabled = true;
            output.textContent = 'Thinking...';

            try {
                const payload = {
                    query,
                    pet_id: petSelect.value || null,
                    max_iterations: Number(iterationsEl.value || 5)
                };

                const res = await fetch('/api/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();

                if (!res.ok || data.status !== 'success') {
                    output.textContent = `Error: ${data.message || 'Unknown error'}`;
                } else {
                    output.textContent = data.response || '(No response text)';
                }
            } catch (err) {
                output.textContent = `Request failed: ${err}`;
            } finally {
                askBtn.disabled = false;
            }
        });

        loadPets();
    </script>
</body>
</html>
        """)

@app.route("/api/query", methods=["POST"])
def query():
    """
    Main endpoint for agent queries
    
    Request body:
    {
        "query": "What natural remedies help with joint pain?",
        "pet_id": "pet_001",  # optional
        "max_iterations": 5    # optional
    }
    
    Response:
    {
        "status": "success",
        "response": "...",
        "pet_id": "pet_001"
    }
    """
    started = time.perf_counter()
    with TRACER.start_as_current_span("api.query") as span:
        try:
            data = request.get_json()
        
            if not data or "query" not in data:
                return jsonify({
                    "status": "error",
                    "message": "Missing 'query' field in request"
                }), 400
        
            query_text = data.get("query")
            pet_id = data.get("pet_id")
            max_iterations = data.get("max_iterations", 5)
            span.set_attribute("petdigitwin.pet_id", pet_id or "")
            span.set_attribute("petdigitwin.max_iterations", max_iterations)
            span.set_attribute("petdigitwin.query_length", len(query_text or ""))
        
            # Run the agent
            response = agent.run(query_text, pet_id=pet_id, max_iterations=max_iterations)
            latency_ms = int((time.perf_counter() - started) * 1000)
            span.set_attribute("petdigitwin.latency_ms", latency_ms)
            span.set_attribute("petdigitwin.success", True)

            run_doc = {
                "ts": datetime.now(timezone.utc),
                "pet_id": pet_id,
                "query": query_text,
                "response": response,
                "max_iterations": max_iterations,
                "latency_ms": latency_ms,
                "success": True,
                "use_vertex_sdk": os.getenv("USE_VERTEX_SDK", "false").lower() == "true",
            }
            db.db.agent_runs.insert_one(run_doc)
        
            return jsonify({
                "status": "success",
                "response": response,
                "pet_id": pet_id,
                "latency_ms": latency_ms,
            })

        except Exception as e:
            latency_ms = int((time.perf_counter() - started) * 1000)
            span.set_attribute("petdigitwin.latency_ms", latency_ms)
            span.set_attribute("petdigitwin.success", False)
            span.record_exception(e)
            try:
                db.db.agent_runs.insert_one({
                    "ts": datetime.now(timezone.utc),
                    "query": (data or {}).get("query") if 'data' in locals() else None,
                    "pet_id": (data or {}).get("pet_id") if 'data' in locals() else None,
                    "response": None,
                    "latency_ms": latency_ms,
                    "success": False,
                    "error": str(e),
                })
            except Exception:
                pass

            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

@app.route("/api/observability/status", methods=["GET"])
def observability_status():
    """Return Arize/OpenInference integration status and basic metrics."""
    try:
        obs = get_observability_status()
        run_count = db.db.agent_runs.count_documents({})
        feedback_count = db.db.agent_feedback.count_documents({})
        return jsonify({
            "status": "success",
            "observability": obs,
            "runtime": {
                "agent_runs": run_count,
                "feedback_entries": feedback_count,
            },
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/observability/feedback", methods=["POST"])
def observability_feedback():
    """Capture user/judge feedback for self-improvement tracking."""
    try:
        payload = request.get_json() or {}
        rating = int(payload.get("rating", 0))
        if rating < 1 or rating > 5:
            return jsonify({"status": "error", "message": "rating must be 1..5"}), 400

        feedback_doc = {
            "ts": datetime.now(timezone.utc),
            "query": payload.get("query"),
            "response": payload.get("response"),
            "pet_id": payload.get("pet_id"),
            "rating": rating,
            "comment": payload.get("comment", ""),
            "tags": payload.get("tags", []),
        }
        db.db.agent_feedback.insert_one(feedback_doc)
        return jsonify({"status": "success", "message": "feedback captured"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/observability/self-improvement-report", methods=["GET"])
def self_improvement_report():
    """Build a compact quality report from runs + feedback for iterative tuning."""
    try:
        window = int(request.args.get("window", 100))
        runs = list(db.db.agent_runs.find({}, {"_id": 0}).sort("ts", -1).limit(window))
        feedback = list(db.db.agent_feedback.find({}, {"_id": 0}).sort("ts", -1).limit(window))

        run_count = len(runs)
        error_count = sum(1 for r in runs if not r.get("success", False))
        avg_latency = int(sum(r.get("latency_ms", 0) for r in runs) / run_count) if run_count else 0

        ratings = [int(f.get("rating", 0)) for f in feedback if f.get("rating")]
        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None
        low_rated = [f for f in feedback if int(f.get("rating", 0)) <= 2]

        recommendations = []
        if run_count and (error_count / run_count) > 0.1:
            recommendations.append("Investigate top failing prompts and add guardrails for missing pet_id/context.")
        if avg_latency > 3500:
            recommendations.append("Reduce prompt/tool context size or cache frequent lookups to lower latency.")
        if avg_rating is not None and avg_rating < 4.0:
            recommendations.append("Use low-rated interactions to build eval datasets and tune prompt instructions.")
        if not recommendations:
            recommendations.append("Quality looks stable; continue collecting feedback and run weekly evals.")

        return jsonify({
            "status": "success",
            "window": window,
            "metrics": {
                "run_count": run_count,
                "error_count": error_count,
                "error_rate": round((error_count / run_count), 4) if run_count else 0,
                "avg_latency_ms": avg_latency,
                "feedback_count": len(feedback),
                "avg_rating": avg_rating,
                "low_rated_count": len(low_rated),
            },
            "recommendations": recommendations,
            "examples_for_review": low_rated[:5],
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/food-recommendations", methods=["GET"])
def food_recommendations():
    """Return food recommendations for a pet."""
    try:
        pet_id = request.args.get("pet_id")
        budget = int(request.args.get("budget", 100))
        if not pet_id:
            return jsonify({"status": "error", "message": "pet_id required"}), 400
        from src.tools import PetDigiTwinTools
        result = json.loads(PetDigiTwinTools().find_suitable_food(pet_id=pet_id, budget=budget))
        return jsonify({"status": "success", **result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/health-knowledge", methods=["GET"])
def health_knowledge():
    """Search vet knowledge base."""
    try:
        condition = request.args.get("condition", "")
        from src.tools import PetDigiTwinTools
        result = json.loads(PetDigiTwinTools().search_health_knowledge(condition=condition))
        return jsonify({"status": "success", **result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/checkup-prediction", methods=["GET"])
def checkup_prediction():
    """Return checkup prediction for a pet."""
    try:
        pet_id = request.args.get("pet_id")
        if not pet_id:
            return jsonify({"status": "error", "message": "pet_id required"}), 400
        from src.tools import PetDigiTwinTools
        result = json.loads(PetDigiTwinTools().predict_checkup_need(pet_id=pet_id))
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/find-volunteers", methods=["GET"])
def find_volunteers():
    """Find volunteers for a pet within a date range."""
    try:
        pet_id        = request.args.get("pet_id")
        start_date    = request.args.get("start_date", "2026-07-01")
        end_date      = request.args.get("end_date",   "2026-07-15")
        max_distance  = int(request.args.get("max_distance_km", 50))
        if not pet_id:
            return jsonify({"status": "error", "message": "pet_id required"}), 400
        from src.tools import PetDigiTwinTools
        result = json.loads(PetDigiTwinTools().find_volunteers_for_pet(
            pet_id=pet_id, start_date=start_date, end_date=end_date,
            max_distance_km=max_distance
        ))
        return jsonify({"status": "success", **result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/pets", methods=["GET"])
def list_pets():
    """List all available pets"""
    try:
        pets = list(db.db.pets.find({}, {
            "_id": 0,
            "id": 1,
            "name": 1,
            "breed": 1,
            "age": 1,
            "conditions": 1,
            "owner_name": 1
        }))
        
        return jsonify({
            "status": "success",
            "pets": pets,
            "count": len(pets)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/api/pets/<pet_id>", methods=["GET"])
def get_pet(pet_id):
    """Get enriched pet health profile."""
    try:
        from src.tools import PetDigiTwinTools
        result = json.loads(PetDigiTwinTools().get_pet_health_summary(pet_id=pet_id))
        if result.get("status") == "error":
            return jsonify(result), 404
        # Merge raw pet doc so UI gets full data
        raw = db.db.pets.find_one({"id": pet_id}, {"_id": 0})
        if raw:
            result.update(raw)
        return jsonify({"status": "success", "pet": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/volunteers", methods=["GET"])
def list_volunteers():
    """List all available volunteers"""
    try:
        volunteers = list(db.db.volunteers.find({}, {
            "_id": 0,
            "id": 1,
            "name": 1,
            "experience_breeds": 1,
            "rating": 1,
            "price_per_day": 1,
            "bio": 1
        }))
        
        return jsonify({
            "status": "success",
            "volunteers": volunteers,
            "count": len(volunteers)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/api/foods", methods=["GET"])
def list_foods():
    """List all available pet foods"""
    try:
        foods = list(db.db.pet_foods.find({}, {
            "_id": 0,
            "id": 1,
            "name": 1,
            "brand": 1,
            "price": 1,
            "suitable_for": 1,
            "breed_specific": 1
        }))
        
        return jsonify({
            "status": "success",
            "foods": foods,
            "count": len(foods)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/api/knowledge", methods=["GET"])
def list_knowledge():
    """List veterinary knowledge base"""
    try:
        condition = request.args.get("condition")
        
        query = {} if not condition else {"condition": {"$regex": condition, "$options": "i"}}
        
        knowledge = list(db.db.vet_knowledge.find(query, {
            "_id": 0,
            "condition": 1,
            "title": 1,
            "natural_remedies": 1
        }))
        
        return jsonify({
            "status": "success",
            "knowledge": knowledge,
            "count": len(knowledge)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
