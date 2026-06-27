/**
 * FinEdge — Edge SDK Simulation Engine
 * =====================================
 * Demonstrates on-device privacy-preserving feature extraction:
 *
 * 1. Bloom Filter    — Probabilistic membership test rejecting
 *                      non-whitelisted SMS sender IDs in O(1).
 * 2. Regex Parser    — Extracts financial metadata from matched
 *                      SMS strings (debits, credits, balances).
 * 3. RAM Purge       — Explicitly nulls raw string references
 *                      after extraction (zero-knowledge principle).
 * 4. HMAC-SHA256     — Signs the JSON vector using WebCrypto API.
 * 5. Network         — POSTs signed vector + signature header to
 *                      the Django scoring backend.
 *
 * All processing happens locally in the browser — raw SMS content
 * never leaves the device.
 */

// ═══════════════════════════════════════════════════════════════════════════
// 1. BLOOM FILTER — Probabilistic Sender-ID Whitelist
// ═══════════════════════════════════════════════════════════════════════════

class BloomFilter {
  /**
   * @param {number} size   — Bit array size (default: 1024)
   * @param {number} hashes — Number of hash functions (default: 3)
   */
  constructor(size = 1024, hashes = 3) {
    this.size = size;
    this.hashes = hashes;
    this.bitArray = new Uint8Array(size);
  }

  /** FNV-1a inspired hash with seed mixing. */
  _hash(value, seed) {
    let hash = 2166136261 ^ seed;
    for (let i = 0; i < value.length; i++) {
      hash ^= value.charCodeAt(i);
      hash = Math.imul(hash, 16777619);
    }
    return Math.abs(hash) % this.size;
  }

  /** Insert a sender ID into the filter. */
  add(value) {
    const upper = value.toUpperCase().trim();
    for (let i = 0; i < this.hashes; i++) {
      const idx = this._hash(upper, i);
      this.bitArray[idx] = 1;
    }
  }

  /** Test membership — may return false positives, never false negatives. */
  test(value) {
    const upper = value.toUpperCase().trim();
    for (let i = 0; i < this.hashes; i++) {
      const idx = this._hash(upper, i);
      if (this.bitArray[idx] === 0) return false;
    }
    return true;
  }

  /** Bulk-insert an array of sender IDs. */
  addAll(values) {
    values.forEach((v) => this.add(v));
  }
}

// Pre-populated whitelist of known financial/utility sender IDs
const WHITELISTED_SENDERS = [
  "HDFCBK", "SBIINB", "ICICIB", "AXISBK", "KOTAKB",
  "KSEBBL", "BSNLMB", "JIOFIN", "PAYTMB", "PHONEPE",
  "GPAY",   "AMZNIN", "FREERC", "AIRTEL", "TATADG",
  "BESCOM", "MSEDCL", "DGVCL",  "CESCLT", "ULOANS",
];

const senderFilter = new BloomFilter(2048, 4);
senderFilter.addAll(WHITELISTED_SENDERS);


// ═══════════════════════════════════════════════════════════════════════════
// 2. REGEX PARSER — Financial SMS Metadata Extraction
// ═══════════════════════════════════════════════════════════════════════════

/** Patterns that identify financial transactions in SMS content. */
const FINANCIAL_PATTERNS = {
  debit: /(?:debited|withdrawn|paid|spent)\s*(?:INR|Rs\.?|₹)\s*[\d,]+\.?\d*/gi,
  credit: /(?:credited|received|deposited)\s*(?:INR|Rs\.?|₹)\s*[\d,]+\.?\d*/gi,
  balance: /(?:bal(?:ance)?|avl\.?\s*bal)\s*(?:is|:)?\s*(?:INR|Rs\.?|₹)\s*[\d,]+\.?\d*/gi,
  emi: /(?:EMI|instalment|installment)\s*(?:of)?\s*(?:INR|Rs\.?|₹)\s*[\d,]+\.?\d*/gi,
  emi_bounce: /(?:EMI|instalment)\s*(?:bounce|failed|dishono|unpaid|overdue)/gi,
  upi: /(?:UPI|IMPS|NEFT|RTGS)\s*(?:ref|txn|transaction)/gi,
};

/**
 * Extract a mathematical feature vector from an array of SMS objects.
 *
 * @param {Array<{sender: string, body: string, timestamp: string}>} messages
 * @returns {{ features: object, matchedCount: number, rejectedCount: number }}
 */
function extractFeatures(messages) {
  let utilitySmsCount = 0;
  let financialAppsCount = 0;
  let totalBalance = 0;
  let balanceReadings = 0;
  let emiBounces = 0;
  let matchedCount = 0;
  let rejectedCount = 0;
  const seenSenders = new Set();

  for (const msg of messages) {
    // Bloom filter gate — reject non-whitelisted senders in O(1)
    if (!senderFilter.test(msg.sender)) {
      rejectedCount++;
      continue;
    }

    matchedCount++;
    seenSenders.add(msg.sender.toUpperCase());

    const body = msg.body;

    // Count utility/transactional SMS
    if (FINANCIAL_PATTERNS.debit.test(body) || FINANCIAL_PATTERNS.credit.test(body)) {
      utilitySmsCount++;
    }
    // Reset lastIndex after global regex test
    FINANCIAL_PATTERNS.debit.lastIndex = 0;
    FINANCIAL_PATTERNS.credit.lastIndex = 0;

    // Extract balance readings
    const balMatch = body.match(FINANCIAL_PATTERNS.balance);
    if (balMatch) {
      for (const m of balMatch) {
        const num = m.replace(/[^0-9.]/g, "");
        const val = parseFloat(num);
        if (!isNaN(val)) {
          totalBalance += val;
          balanceReadings++;
        }
      }
    }

    // Detect EMI bounces
    if (FINANCIAL_PATTERNS.emi_bounce.test(body)) {
      emiBounces++;
    }
    FINANCIAL_PATTERNS.emi_bounce.lastIndex = 0;
  }

  // Derive financial_apps_count from unique sender diversity
  financialAppsCount = seenSenders.size;

  // Average monthly balance (simple average of all balance readings)
  const avgBalance = balanceReadings > 0 ? totalBalance / balanceReadings : 0;

  return {
    features: {
      utility_sms_count: utilitySmsCount,
      financial_apps_count: financialAppsCount,
      average_monthly_balance: Math.round(avgBalance * 100) / 100,
      lifetime_emi_bounces: emiBounces,
    },
    matchedCount,
    rejectedCount,
  };
}


// ═══════════════════════════════════════════════════════════════════════════
// 3. RAM PURGE — Zero-Knowledge Data Cleanup
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Explicitly dereference raw SMS data from memory.
 * In a real SDK, this would also call platform-specific secure-erase APIs.
 *
 * @param {object} ref — Object whose string properties will be nulled.
 * @returns {string[]}  — List of purged property names (for audit log).
 */
function purgeRawData(ref) {
  const purged = [];
  if (ref && typeof ref === "object") {
    for (const key of Object.keys(ref)) {
      if (typeof ref[key] === "string" || Array.isArray(ref[key])) {
        ref[key] = null;
        purged.push(key);
      }
    }
  }
  return purged;
}


// ═══════════════════════════════════════════════════════════════════════════
// 4. HMAC-SHA256 — WebCrypto Payload Signing
// ═══════════════════════════════════════════════════════════════════════════

/** Dummy client secret (matches Django backend's FINEDGE_HMAC_SECRET). */
const CLIENT_SECRET = "finedge_hmac_shared_secret_2026";

/**
 * Sign a JSON string with HMAC-SHA256 using the WebCrypto API.
 *
 * @param {string} payload — The JSON string to sign.
 * @returns {Promise<string>} — Hex-encoded HMAC digest.
 */
async function signPayload(payload) {
  const encoder = new TextEncoder();
  const keyData = encoder.encode(CLIENT_SECRET);
  const msgData = encoder.encode(payload);

  const cryptoKey = await crypto.subtle.importKey(
    "raw",
    keyData,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );

  const signature = await crypto.subtle.sign("HMAC", cryptoKey, msgData);

  // Convert ArrayBuffer → hex string
  const hashArray = Array.from(new Uint8Array(signature));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}


// ═══════════════════════════════════════════════════════════════════════════
// 5. SYNTHETIC SMS GENERATOR (Demo Data)
// ═══════════════════════════════════════════════════════════════════════════

/** Generate realistic synthetic SMS messages for the simulator demo. */
function generateSyntheticSMS(profile = "average", count = 40) {
  const good_templates = [
    { sender: "HDFCBK", body: "INR 85,000.00 credited to your a/c XX5678 by NEFT. Balance is INR 1,23,450.00" },
    { sender: "SBIINB", body: "Dear Customer, your EMI of INR 8,500 has been debited from a/c XX1234. Avl Bal: INR 1,14,950.00" },
    { sender: "ICICIB", body: "Your a/c XX9012 debited Rs.1,200 for electricity bill payment. Avl Bal Rs.1,13,750.00" },
    { sender: "AXISBK", body: "Rs.5,000.00 credited to your Axis Bank a/c XX3456 via UPI. Bal: Rs.1,18,750.00" },
    { sender: "GPAY", body: "You paid ?1,500.00 to BigBasket using Google Pay. UPI ref GPY123" }
  ];

  const average_templates = [
    { sender: "SBIINB", body: "INR 25,000.00 credited to your a/c XX5678. Balance is INR 35,450.00" },
    { sender: "HDFCBK", body: "Dear Customer, your EMI of INR 4,500 has been debited. Avl Bal: INR 30,950.00" },
    { sender: "AXISBK", body: "EMI bounce alert: Your EMI of INR 4,500 has failed due to insufficient balance" },
    { sender: "AXISBK", body: "Rs.5,000.00 credited to your Axis Bank a/c XX3456. Bal: Rs.35,950.00" },
    { sender: "PAYTMB", body: "?350.00 paid to Zomato via Paytm UPI. Balance: ?35,600.00" }
  ];

  const bad_templates = [
    { sender: "HDFCBK", body: "EMI bounce alert: Your EMI of INR 2,000 has failed due to insufficient balance" },
    { sender: "SBIINB", body: "URGENT: EMI instalment overdue for Loan XX6543. Amount: Rs.5,200." },
    { sender: "ICICIB", body: "Your a/c XX9012 debited Rs.100. Avl Bal Rs.450.00" },
    { sender: "AXISBK", body: "EMI bounce alert: Your EMI of INR 1,500 has failed due to insufficient balance" },
    { sender: "PHONEPE", body: "You paid ?50.00 to Tea Stall via PhonePe. Avl Bal: Rs.400.00" }
  ];

  let templates = average_templates;
  if (profile === "good") templates = good_templates;
  if (profile === "bad") templates = bad_templates;

  const messages = [];
  const now = Date.now();

  for (let i = 0; i < count; i++) {
    const tmpl = templates[i % templates.length];
    messages.push({
      sender: tmpl.sender,
      body: tmpl.body,
      timestamp: new Date(now - i * 3600000).toISOString(),
    });
  }

  return messages;
}


// ═══════════════════════════════════════════════════════════════════════════
// 6. TERMINAL LOGGER — Hacker-Style Console Output
// ═══════════════════════════════════════════════════════════════════════════

class TerminalLogger {
  /**
   * @param {HTMLElement} element — The terminal output container.
   */
  constructor(element) {
    this.el = element;
    this.queue = [];
    this.isProcessing = false;
  }

  /**
   * Queue a log line with optional delay and color.
   * @param {string}  text    — Terminal line text.
   * @param {string}  type    — 'info' | 'success' | 'warning' | 'error' | 'system' | 'data'
   * @param {number}  delay   — Milliseconds to wait before printing (default: 150).
   */
  log(text, type = "info", delay = 150) {
    this.queue.push({ text, type, delay });
    if (!this.isProcessing) this._processQueue();
  }

  /** Clear terminal output. */
  clear() {
    this.el.innerHTML = "";
    this.queue = [];
  }

  async _processQueue() {
    this.isProcessing = true;
    while (this.queue.length > 0) {
      const { text, type, delay } = this.queue.shift();
      await this._wait(delay);
      this._appendLine(text, type);
    }
    this.isProcessing = false;
  }

  _appendLine(text, type) {
    const line = document.createElement("div");
    line.className = `terminal-line terminal-${type}`;

    const prefix = {
      info:    '<span class="terminal-prefix">&gt;</span> ',
      success: '<span class="terminal-prefix text-green-400">✓</span> ',
      warning: '<span class="terminal-prefix text-yellow-400">⚠</span> ',
      error:   '<span class="terminal-prefix text-red-400">✗</span> ',
      system:  '<span class="terminal-prefix text-cyan-400">⊕</span> ',
      data:    '<span class="terminal-prefix text-purple-400">→</span> ',
    };

    line.innerHTML = (prefix[type] || prefix.info) + this._escapeHtml(text);
    this.el.appendChild(line);
    this.el.scrollTop = this.el.scrollHeight;
  }

  _escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  _wait(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}


// ═══════════════════════════════════════════════════════════════════════════
// 7. ORCHESTRATOR — Full Edge Pipeline Execution
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Run the complete edge extraction → sign → transmit pipeline.
 *
 * @param {TerminalLogger} terminal — Terminal logger instance.
 * @param {string}         apiUrl   — Django backend scoring endpoint URL.
 * @param {number}         requestedAmount — The loan amount requested by the user.
 * @param {object}         uiCallbacks — { onScoreReceived, onError, onComplete }
 */
async function runEdgePipeline(terminal, apiUrl, requestedAmount, profile, uiCallbacks = {}) {
  const startTime = performance.now();

  try {
    // ── Phase 1: Generate synthetic SMS (simulates reading device inbox) ──
    terminal.log("Initialising FinEdge SDK v1.0.0 ...", "system", 300);
    terminal.log("Requesting SMS inbox access (read-only) ...", "info", 400);
    terminal.log("DPDP Act consent verified ✓", "success", 300);
    terminal.log("", "info", 100);

    terminal.log("═══ PHASE 1: LOCAL DATA ACQUISITION ═══", "system", 400);
    let rawMessages = generateSyntheticSMS(profile, 40);
    terminal.log(`Loaded ${rawMessages.length} SMS messages from device inbox`, "info", 350);

    // ── Phase 2: Bloom filter scan ───────────────────────────────────────
    terminal.log("", "info", 100);
    terminal.log("═══ PHASE 2: BLOOM FILTER SCAN ═══", "system", 400);
    terminal.log(`Bloom filter initialised (size=2048, k=4 hash functions)`, "info", 250);
    terminal.log(`Whitelisted sender IDs: ${WHITELISTED_SENDERS.length}`, "info", 200);
    terminal.log("Scanning local SMS array against bloom filter ...", "info", 500);

    const { features: partialFeatures, matchedCount, rejectedCount } = extractFeatures(rawMessages);

    terminal.log(`Bloom filter complete:`, "success", 300);
    terminal.log(`  Matched (whitelisted):  ${matchedCount} messages`, "data", 150);
    terminal.log(`  Rejected (spam/unknown): ${rejectedCount} messages`, "data", 150);

    // ── Phase 3: Regex extraction ────────────────────────────────────────
    terminal.log("", "info", 100);
    terminal.log("═══ PHASE 3: REGEX FEATURE EXTRACTION ═══", "system", 400);
    terminal.log("Applying financial regex patterns ...", "info", 400);
    terminal.log("  Pattern: /debited|withdrawn|paid/ ... scanning", "info", 200);
    terminal.log("  Pattern: /credited|received|deposited/ ... scanning", "info", 200);
    terminal.log("  Pattern: /EMI.*bounce|failed|overdue/ ... scanning", "info", 200);
    terminal.log("  Pattern: /bal(?:ance)?.*INR|Rs/ ... scanning", "info", 200);
    terminal.log("Regex extraction complete ✓", "success", 300);

    // ── Phase 4: Construct full feature vector ───────────────────────────
    terminal.log("", "info", 100);
    terminal.log("═══ PHASE 4: VECTOR CONSTRUCTION ═══", "system", 400);

    // Add simulated device-level features
    const deviceAge = 180 + Math.floor(Math.random() * 500);
    const batteryDeaths = Math.floor(Math.random() * 4);
    const contactsRatio = Math.round((0.2 + Math.random() * 0.5) * 10000) / 10000;

    const mathematicalVector = {
      device_age_days: deviceAge,
      utility_sms_count: partialFeatures.utility_sms_count,
      battery_deaths_weekly: batteryDeaths,
      saved_contacts_ratio: contactsRatio,
      financial_apps_count: partialFeatures.financial_apps_count,
      average_monthly_balance: partialFeatures.average_monthly_balance,
      lifetime_emi_bounces: partialFeatures.lifetime_emi_bounces,
    };

    terminal.log("Mathematical vector constructed:", "success", 250);
    for (const [key, val] of Object.entries(mathematicalVector)) {
      terminal.log(`  ${key}: ${val}`, "data", 100);
    }

    // ── Phase 5: RAM Purge ───────────────────────────────────────────────
    terminal.log("", "info", 100);
    terminal.log("═══ PHASE 5: RAM PURGE (ZERO-KNOWLEDGE) ═══", "system", 400);
    terminal.log("Purging raw SMS content from memory ...", "warning", 350);

    const dataRef = { messages: rawMessages, rawBodies: rawMessages.map(m => m.body) };
    const purgedKeys = purgeRawData(dataRef);
    rawMessages = null; // Explicit null assignment

    for (const key of purgedKeys) {
      terminal.log(`  Purged: ${key} → null`, "warning", 120);
    }
    terminal.log("Raw data dereferenced — only integer vector remains ✓", "success", 300);
    terminal.log("Privacy guarantee: raw SMS never leaves device ✓", "success", 200);

    // ── Phase 6: HMAC Signing ────────────────────────────────────────────
    terminal.log("", "info", 100);
    terminal.log("═══ PHASE 6: CRYPTOGRAPHIC SIGNING ═══", "system", 400);
    terminal.log("Generating HMAC-SHA256 signature via WebCrypto API ...", "info", 500);

    const payload = {
      device_hash_mask: await _generateDeviceHash(),
      tracking_reference: `FINEDGE-SIM-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      requested_amount: requestedAmount,
      mathematical_vector: mathematicalVector,
    };

    const payloadJson = JSON.stringify(payload);
    const signature = await signPayload(payloadJson);

    terminal.log(`Payload size: ${payloadJson.length} bytes`, "data", 200);
    terminal.log(`HMAC-SHA256: ${signature.substring(0, 32)}...`, "data", 200);
    terminal.log("Vector cryptographically signed ✓", "success", 300);

    // ── Phase 7: Network transmission ────────────────────────────────────
    terminal.log("", "info", 100);
    terminal.log("═══ PHASE 7: SECURE TRANSMISSION ═══", "system", 400);
    terminal.log(`POST → ${apiUrl}`, "info", 300);
    terminal.log("Headers: Authorization: Api-Key ••••••••", "info", 150);
    terminal.log("Headers: X-FinEdge-Signature: " + signature.substring(0, 16) + "...", "info", 150);
    terminal.log("Transmitting signed vector (raw data NOT included) ...", "info", 500);

    let response;
    try {
      response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Api-Key finedge_demo_api_key_2026",
          "X-FinEdge-Signature": signature,
        },
        body: payloadJson,
      });

      const result = await response.json();

      if (response.ok) {
        terminal.log("", "info", 100);
        terminal.log("═══ RESPONSE RECEIVED ═══", "system", 300);
        terminal.log(`HTTP ${response.status} ${response.statusText}`, "success", 200);
        terminal.log(`Decision: ${result.decision || "N/A"}`, "data", 150);
        terminal.log(`TrustScore: ${result.trust_score || "N/A"}`, "data", 150);
        terminal.log(`Application ID: ${result.application_id || "N/A"}`, "data", 150);

        if (result.default_probability !== null && result.default_probability !== undefined) {
          terminal.log(`Default Probability: ${(result.default_probability * 100).toFixed(2)}%`, "data", 150);
        }

        if (uiCallbacks.onScoreReceived) {
          uiCallbacks.onScoreReceived(result);
        }
      } else {
        terminal.log(`HTTP ${response.status}: ${result.error || "Request failed"}`, "error", 200);
        terminal.log(`Detail: ${result.detail || JSON.stringify(result)}`, "error", 150);

        // Still display the vector for demo purposes
        if (uiCallbacks.onScoreReceived) {
          uiCallbacks.onScoreReceived({
            decision: "DEMO_MODE",
            trust_score: _calculateLocalFallbackScore(mathematicalVector),
            default_probability: null,
            is_thin_file: mathematicalVector.device_age_days < 14,
            model_version: "local-fallback",
            waterfall_step: 0,
            demo_note: "Backend unavailable — score computed locally for demo.",
          });
        }
      }
    } catch (networkErr) {
      terminal.log(`Network error: ${networkErr.message}`, "error", 200);
      terminal.log("Backend unavailable — computing local fallback score ...", "warning", 300);

      const fallbackScore = _calculateLocalFallbackScore(mathematicalVector);
      terminal.log(`Local fallback TrustScore: ${fallbackScore}`, "data", 200);

      if (uiCallbacks.onScoreReceived) {
        uiCallbacks.onScoreReceived({
          decision: "DEMO_MODE",
          trust_score: fallbackScore,
          default_probability: null,
          is_thin_file: mathematicalVector.device_age_days < 14,
          model_version: "local-fallback",
          waterfall_step: 0,
          demo_note: "Backend unavailable — score computed locally for demo.",
        });
      }
    }

    // ── Complete ─────────────────────────────────────────────────────────
    const elapsed = ((performance.now() - startTime) / 1000).toFixed(2);
    terminal.log("", "info", 100);
    terminal.log("═══════════════════════════════════════════", "system", 200);
    terminal.log(`Pipeline complete in ${elapsed}s`, "success", 200);
    terminal.log("All raw data purged — zero-knowledge guarantee maintained ✓", "success", 200);
    terminal.log("═══════════════════════════════════════════", "system", 200);

    if (uiCallbacks.onComplete) uiCallbacks.onComplete();

  } catch (err) {
    terminal.log(`Fatal error: ${err.message}`, "error", 0);
    console.error("FinEdge pipeline error:", err);
    if (uiCallbacks.onError) uiCallbacks.onError(err);
  }
}


// ═══════════════════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════════════════

/** Generate a SHA-256 hash of simulated device identifiers. */
async function _generateDeviceHash() {
  const raw = `device-${navigator.userAgent}-${screen.width}x${screen.height}-${Date.now()}`;
  const encoded = new TextEncoder().encode(raw);
  const hashBuffer = await crypto.subtle.digest("SHA-256", encoded);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}

/**
 * Simple local fallback score when the backend is unavailable.
 * Uses a basic heuristic (NOT the trained XGBoost model).
 */
function _calculateLocalFallbackScore(vector) {
  let score = 600; // Base score
  score += Math.min(vector.device_age_days / 10, 50);
  score += Math.min(vector.utility_sms_count * 3, 60);
  score -= vector.battery_deaths_weekly * 10;
  score += vector.saved_contacts_ratio * 80;
  score += Math.min(vector.financial_apps_count * 8, 40);
  score += Math.min(vector.average_monthly_balance / 2000, 50);
  score -= vector.lifetime_emi_bounces * 30;
  return Math.max(300, Math.min(900, Math.round(score)));
}


// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS (for use in index.html)
// ═══════════════════════════════════════════════════════════════════════════

// Attach to window for non-module script usage
window.FinEdge = {
  BloomFilter,
  TerminalLogger,
  extractFeatures,
  purgeRawData,
  signPayload,
  generateSyntheticSMS,
  runEdgePipeline,
};
