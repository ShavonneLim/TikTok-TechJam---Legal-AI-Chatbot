from pymongo import MongoClient, UpdateOne
from datetime import datetime
import os

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/RAG")
client = MongoClient(MONGO_URI)
db = client.get_database()
col = db["data"]

# Ensure unique index so we don't duplicate entries
col.create_index("feature_name", unique=True, name="uniq_feature_name")

docs = [
    {"feature_name": "Curfew login blocker with ASL and GH for Utah minors", "feature_description": "To comply with the Utah Social Media Regulation Act, we are implementing a curfew-based login restriction for users under 18. The system uses ASL to detect minor accounts and routes enforcement through GH to apply only within Utah boundaries. The feature activates during restricted night hours and logs activity using EchoTrace for auditability. This allows parental control to be enacted without user-facing alerts, operating in ShadowMode during initial rollout."},
    {"feature_name": "PF default toggle with NR enforcement for California teens", "feature_description": "As part of compliance with California’s SB976, the app will disable PF by default for users under 18 located in California. This default setting is considered NR to override, unless explicit parental opt-in is provided. Geo-detection is handled via GH, and rollout is monitored with FR logs. The design ensures minimal disruption while meeting the strict personalization requirements imposed by the law."},
    {"feature_name": "Child abuse content scanner using T5 and CDS triggers", "feature_description": "In line with the US federal law requiring providers to report child sexual abuse content to NCMEC, this feature scans uploads and flags suspected materials tagged as T5. Once flagged, the CDS auto-generates reports and routes them via secure channel APIs. The logic runs in real-time, supports human validation, and logs detection metadata for internal audits. Regional thresholds are governed by LCP parameters in the backend."},
    {"feature_name": "Content visibility lock with NSP for EU DSA", "feature_description": "To meet the transparency expectations of the EU Digital Services Act, we are introducing a visibility lock for flagged user-generated content labeled under NSP. When such content is detected, a soft Softblock is applied and GH ensures enforcement is restricted to the EU region only. EchoTrace supports traceability, and Redline status can be triggered for legal review. This feature enhances accountability and complies with Article 16’s removal mechanisms."},
    {"feature_name": "Jellybean-based parental notifications for Florida regulation", "feature_description": "To support Florida's Online Protections for Minors law, this feature extends the Jellybean parental control framework. Notifications are dispatched to verified parent accounts when a minor attempts to access restricted features. Using IMT, the system checks behavioral anomalies against BB models. If violations are detected, restrictions are applied in ShadowMode with full audit logging through CDS. Glow flags ensure compliance visibility during rollout phases."},
    {"feature_name": "Unified retention control via DRT & CDS", "feature_description": "Introduce a data retention feature using DRT thresholds, ensuring automatic log deletion across all regions. CDS will continuously audit retention violations, triggering EchoTrace as necessary. Spanner logic ensures all platform modules comply uniformly."},
    {"feature_name": "NSP auto-flagging", "feature_description": "This feature will automatically detect and tag content that violates NSP policy. Once flagged, Softblock is applied and a Redline alert is generated if downstream sharing is attempted."},
    {"feature_name": "T5 tagging for sensitive reports", "feature_description": "When users report content containing high-risk information, it is tagged as T5 for internal routing. CDS then enforces escalation. The system is universal and does not rely on regional toggles or GH routes."},
    {"feature_name": "Underage protection via Snowcap trigger", "feature_description": "Snowcap is activated for all underage users platform-wide, applying ASL to segment accounts. Actions taken under this logic are routed to CDS and monitored using BB to identify deviations in usage."},
    {"feature_name": "Universal PF deactivation on guest mode", "feature_description": "By default, PF will be turned off for all uses browsing in guest mode."},
    {"feature_name": "Story resharing with content expiry", "feature_description": "Enable users to reshare stories from others, with auto-expiry after 48 hours. This feature logs resharing attempts with EchoTrace and stores activity under BB."},
    {"feature_name": "Leaderboard system for weekly creators", "feature_description": "Introduce a creator leaderboard updated weekly using internal analytics. Points and rankings are stored in FR metadata and tracked using IMT."},
    {"feature_name": "Mood-based PF enhancements", "feature_description": "Adjust PF recommendations based on inferred mood signals from emoji usage. This logic is soft-tuned using BB and undergoes quiet testing in ShadowMode."},
    {"feature_name": "New user rewards via NR profile suggestions", "feature_description": "At onboarding, users will receive NR-curated profiles to follow for faster network building. A/B testing will use Spanner."},
    {"feature_name": "Creator fund payout tracking in CDS", "feature_description": "Monetization events will be tracked through CDS to detect anomalies in creator payouts. DRT rules apply for log trimming."},
    {"feature_name": "Trial run of video replies in EU", "feature_description": "Roll out video reply functionality to users in EEA only. GH will manage exposure control, and BB is used to baseline feedback."},
    {"feature_name": "Canada-first PF variant test", "feature_description": "Launch a PF variant in CA as part of early experimentation. Spanner will isolate affected cohorts and Glow flags will monitor feature health."},
    {"feature_name": "Chat UI overhaul", "feature_description": "A new chat layout will be tested in the following regions: CA, US, BR, ID. GH will ensure location targeting and ShadowMode will collect usage metrics without user impact."},
    {"feature_name": "Regional trial of autoplay behavior", "feature_description": "Enable video autoplay only for users in US. GH filters users, while Spanner logs click-through deltas."},
    {"feature_name": "South Korea dark theme A/B experiment", "feature_description": "A/B test dark theme accessibility for users in South Korea. Rollout is limited via GH and monitored with FR flags."},
    {"feature_name": "Age-specific notification controls with ASL", "feature_description": "Notifications will be tailored by age using ASL, allowing us to throttle or suppress push alerts for minors. EchoTrace will log adjustments, and CDS will verify enforcement across rollout waves."},
    {"feature_name": "Chat content restrictions via LCP", "feature_description": "Enforce message content constraints by injecting LCP rules on delivery. ShadowMode will initially deploy the logic for safe validation. No explicit mention of legal requirements, but privacy context is implied."},
    {"feature_name": "Video upload limits for new users", "feature_description": "Introduce limits on video uploads from new accounts. IMT will trigger thresholds based on BB patterns. These limitations are partly for platform safety but without direct legal mapping."},
    {"feature_name": "Flag escalation flow for sensitive comments", "feature_description": "A flow that detects high-risk comment content and routes it via CDS with Redline markers. The logic applies generally and is monitored through EchoTrace, with no mention of regional policies."},
    {"feature_name": "User behavior scoring for policy gating", "feature_description": "Behavioral scoring via Spanner will be used to gate access to certain tools. The feature tracks usage and adjusts gating based on BB divergence."},
    {"feature_name": "Minor-safe chat expansion via Jellybean", "feature_description": "We’re expanding chat features, but for users flagged by Jellybean, certain functions (e.g., media sharing) will be limited. BB and ASL will monitor compliance posture."},
    {"feature_name": "Friend suggestions with underage safeguards", "feature_description": "New suggestion logic uses PF to recommend friends, but minors are excluded from adult pools using ASL and CDS logic. EchoTrace logs interactions in case future policy gates are needed."},
    {"feature_name": "Reaction GIFs with embedded filtering", "feature_description": "Enable GIFs in comments, while filtering content deemed inappropriate for minor accounts. Softblock will apply if a flagged GIF is used by ASL-flagged profiles."},
    {"feature_name": "Longform posts with age-based moderation", "feature_description": "Longform post creation is now open to all. However, moderation for underage authors is stricter via Snowcap."},
    {"feature_name": "Custom avatar system with identity checks", "feature_description": "Users can now design custom avatars. For safety, T5 triggers block adult-themed assets from use by underage profiles. Age detection uses ASL and logs flow through GH."}
]

ops = []
now = datetime.utcnow()
for d in docs:
    d["updated_at"] = now
    ops.append(UpdateOne({"feature_name": d["feature_name"]}, {"$set": d}, upsert=True))

result = col.bulk_write(ops, ordered=False)
print("Upserts complete.")
print("matched:", result.matched_count, "modified:", result.modified_count, "upserts:", len(result.upserted_ids or {}))