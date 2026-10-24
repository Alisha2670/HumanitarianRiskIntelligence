/**
 * DASHBOARD MODULE - DYNAMIC INTELLIGENCE
 * 
 * Computes live metric aggregates from stored prediction history
 * and powers the dynamic recent assessments feed.
 */

// 1. Immediately secure the page!
Auth.protectRoute();

// Helper: Format Relative Time
function formatRelativeTime(isoString) {
    if (!isoString) return "Recently";
    const then = new Date(isoString).getTime();
    const now = Date.now();
    const diffSecs = Math.max(0, Math.floor((now - then) / 1000));

    if (diffSecs < 60) return "Just now";
    const diffMins = Math.floor(diffSecs / 60);
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays}d ago`;

    return new Date(isoString).toLocaleDateString("en-IN", {
        month: "short",
        day: "numeric"
    });
}

// Helper: Get Uniform Badge Class
function getBadgeClass(riskLevel) {
    const lower = (riskLevel || "").toLowerCase();
    if (lower.includes("high") || lower.includes("critical") || lower.includes("poor")) {
        return "risk-badge poor";
    }
    if (lower.includes("moderate") || lower.includes("medium")) {
        return "risk-badge moderate";
    }
    return "risk-badge good";
}

// -------------------------------------------------------------
// 1. DYNAMIC METRICS FROM LOCAL PREDICTION HISTORY
// -------------------------------------------------------------
function updateDynamicMetrics() {
    const rawHistory = localStorage.getItem("ecovision_history");
    const history = rawHistory ? JSON.parse(rawHistory) : [];

    // --- A. Total Predictions & Trend ---
    const totalEl = document.getElementById("dash-total-predictions");
    const trendEl = document.getElementById("dash-predictions-trend");

    if (totalEl) {
        totalEl.textContent = history.length;
    }

    if (trendEl) {
        if (history.length === 0) {
            trendEl.innerHTML = `
                <i data-feather="inbox" style="width: 14px; height: 14px;"></i>
                <span>0 logged tests</span>
            `;
        } else {
            const sevenDaysAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
            const weekCount = history.filter(item => {
                const t = new Date(item.timestamp).getTime();
                return !isNaN(t) && t >= sevenDaysAgo;
            }).length;

            trendEl.innerHTML = `
                <i data-feather="arrow-up" style="width: 14px; height: 14px; color: var(--risk-low);"></i>
                <span style="color: var(--risk-low); font-weight: 500;">${weekCount} this week</span>
            `;
        }
    }

    // --- B. Average Air Risk ---
    const airRiskEl = document.getElementById("dash-avg-air-risk");
    const airRiskSubEl = document.getElementById("dash-air-risk-sub");

    const airRecords = history.filter(item => (item.module || "").toLowerCase().includes("air"));

    if (airRiskEl && airRiskSubEl) {
        if (airRecords.length === 0) {
            airRiskEl.textContent = "No Data";
            airRiskEl.style.color = "var(--text-muted)";
            airRiskSubEl.textContent = "No air scans performed yet";
        } else {
            // Score mapping: Low/Good = 1, Moderate = 2, High/Poor = 3
            let scoreSum = 0;
            airRecords.forEach(r => {
                const lvl = (r.riskLevel || "").toLowerCase();
                if (lvl.includes("poor") || lvl.includes("high")) scoreSum += 3;
                else if (lvl.includes("moderate") || lvl.includes("medium")) scoreSum += 2;
                else scoreSum += 1;
            });

            const avgScore = scoreSum / airRecords.length;
            if (avgScore > 2.3) {
                airRiskEl.textContent = "Poor";
                airRiskEl.style.color = "var(--risk-high)";
            } else if (avgScore >= 1.7) {
                airRiskEl.textContent = "Moderate";
                airRiskEl.style.color = "var(--risk-med)";
            } else {
                airRiskEl.textContent = "Good";
                airRiskEl.style.color = "var(--risk-low)";
            }

            airRiskSubEl.textContent = `Calculated across ${airRecords.length} assessment${airRecords.length === 1 ? "" : "s"}`;
        }
    }

    // --- C. Critical Alerts (in last 48 hours) ---
    const critAlertsEl = document.getElementById("dash-critical-alerts");
    const critAlertsSubEl = document.getElementById("dash-critical-alerts-sub");

    if (critAlertsEl && critAlertsSubEl) {
        const fortyEightHoursAgo = Date.now() - 48 * 60 * 60 * 1000;
        const criticalItems = history.filter(item => {
            const t = new Date(item.timestamp).getTime();
            const isRecent = !isNaN(t) && t >= fortyEightHoursAgo;
            const lvl = (item.riskLevel || "").toLowerCase();
            const isCritical = lvl.includes("high") || lvl.includes("critical") || lvl.includes("poor");
            return isRecent && isCritical;
        });

        critAlertsEl.textContent = criticalItems.length;

        if (criticalItems.length > 0) {
            critAlertsEl.style.color = "var(--risk-high)";
            critAlertsSubEl.textContent = `${criticalItems.length} active high-threat alert${criticalItems.length === 1 ? "" : "s"} (48h)`;
            critAlertsSubEl.style.color = "var(--risk-high)";
            critAlertsSubEl.style.fontWeight = "600";
        } else {
            critAlertsEl.style.color = "var(--text-main)";
            critAlertsSubEl.textContent = "All safe (0 alerts in last 48h)";
            critAlertsSubEl.style.color = "var(--text-muted)";
            critAlertsSubEl.style.fontWeight = "normal";
        }
    }

    // --- D. Recent Assessments List ---
    renderRecentAssessments(history);
}

// -------------------------------------------------------------
// 2. RENDER RECENT ASSESSMENTS FEED
// -------------------------------------------------------------
function renderRecentAssessments(history) {
    const container = document.getElementById("recent-assessments-container");
    if (!container) return;

    if (!history || history.length === 0) {
        container.innerHTML = `
            <div class="recent-empty-state">
                <i data-feather="inbox" style="width: 32px; height: 32px; margin-bottom: 8px; color: var(--text-muted);"></i>
                <p style="font-size: 0.95rem; margin-bottom: 12px; color: var(--text-muted);">No risk intelligence scans recorded yet.</p>
                <div style="display: flex; gap: 10px; justify-content: center;">
                    <a href="/templates/air_prediction.html" class="btn btn-outline" style="font-size: 0.85rem; padding: 6px 14px;">Test Air</a>
                    <a href="/templates/water_prediction.html" class="btn btn-outline" style="font-size: 0.85rem; padding: 6px 14px;">Test Water</a>
                </div>
            </div>
        `;
        if (window.feather) feather.replace();
        return;
    }

    // Display the 4 most recent assessments
    const recent = history.slice(-4).reverse();

    let html = `<div class="recent-list">`;
    recent.forEach(item => {
        const isAir = (item.module || "").toLowerCase().includes("air");
        const iconName = isAir ? "wind" : "droplet";
        const iconClass = isAir ? "recent-icon-air" : "recent-icon-water";
        const badgeClass = getBadgeClass(item.riskLevel);
        const relTime = formatRelativeTime(item.timestamp);

        html += `
            <div class="recent-item">
                <div class="recent-item-info">
                    <div class="recent-icon-wrap ${iconClass}">
                        <i data-feather="${iconName}" style="width: 18px; height: 18px;"></i>
                    </div>
                    <div>
                        <strong style="font-size: 0.95rem; display: block; color: var(--text-main);">
                            ${item.location || "Regional Zone"}
                        </strong>
                        <span style="font-size: 0.8rem; color: var(--text-muted);">
                            ${item.module} • ${relTime}
                        </span>
                    </div>
                </div>
                <span class="${badgeClass}">${item.riskLevel || "Assessed"}</span>
            </div>
        `;
    });
    html += `</div>`;

    container.innerHTML = html;
    if (window.feather) feather.replace();
}

// -------------------------------------------------------------
// DOM INITIALIZATION
// -------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    // 1. Personalize greeting from session
    const session = Auth.getSession();
    const nameDisplay = document.getElementById("user-name-display");
    if (nameDisplay && session) {
        nameDisplay.textContent = session.firstName || "Analyst";
    }

    // 2. Logout button handler
    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", e => {
            e.preventDefault();
            Auth.logout();
        });
    }

    // 3. Compute dynamic history metrics and recent activity
    updateDynamicMetrics();

    // 4. Initialize Feather Icons
    if (window.feather) {
        feather.replace();
    }
});
