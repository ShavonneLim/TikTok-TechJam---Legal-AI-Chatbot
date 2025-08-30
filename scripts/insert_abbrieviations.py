from pymongo import MongoClient, UpdateOne
from datetime import datetime
import os

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/RAG")
client = MongoClient(MONGO_URI)
db = client.get_database()
col = db["Abbreviations"]

# 1) Ensure unique index on `term`
col.create_index("term", unique=True, name="uniq_term")

# 2) Your data
docs = [
    {"term": "NR",         "explanation": "Not recommended"},
    {"term": "PF",         "explanation": "Personalized feed"},
    {"term": "GH",         "explanation": "Geo-handler; a module responsible for routing features based on user region"},
    {"term": "CDS",        "explanation": "Compliance Detection System"},
    {"term": "DRT",        "explanation": "Data retention threshold; duration for which logs can be stored"},
    {"term": "LCP",        "explanation": "Local compliance policy"},
    {"term": "Redline",    "explanation": "Flag for legal review (different from its traditional business use for 'financial loss')"},
    {"term": "Softblock",  "explanation": "A user-level limitation applied silently without notifications"},
    {"term": "Spanner",    "explanation": "A synthetic name for a rule engine (not to be confused with Google Spanner)"},
    {"term": "ShadowMode", "explanation": "Deploy feature in non-user-impact way to collect analytics only"},
    {"term": "T5",         "explanation": "Tier 5 sensitivity data; more critical than T1–T4 in this internal taxonomy"},
    {"term": "ASL",        "explanation": "Age-sensitive logic"},
    {"term": "Glow",       "explanation": "A compliance-flagging status, internally used to indicate geo-based alerts"},
    {"term": "NSP",        "explanation": "Non-shareable policy (content should not be shared externally)"},
    {"term": "Jellybean",  "explanation": "Feature name for internal parental control system"},
    {"term": "EchoTrace",  "explanation": "Log tracing mode to verify compliance routing"},
    {"term": "BB",         "explanation": "Baseline Behavior; standard user behavior used for anomaly detection"},
    {"term": "Snowcap",    "explanation": "A synthetic codename for the child safety policy framework"},
    {"term": "FR",         "explanation": "Feature rollout status"},
    {"term": "IMT",        "explanation": "Internal monitoring trigger"},
]

# 3) Upsert all terms (safe to re-run)
ops = []
now = datetime.utcnow()
for d in docs:
    d["updated_at"] = now
    ops.append(UpdateOne({"term": d["term"]}, {"$set": d}, upsert=True))

result = col.bulk_write(ops, ordered=False)
print("Upserts complete.")
print("matched:", result.matched_count, "modified:", result.modified_count, "upserts:", len(result.upserted_ids or {}))
