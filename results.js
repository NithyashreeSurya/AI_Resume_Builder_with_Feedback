const storedPayload = sessionStorage.getItem("resumeBuilderManualResult");
const FLASK_BACKEND_ORIGIN = "http://127.0.0.1:5000";
const API_BASE_URL = ["127.0.0.1:5000", "localhost:5000"].includes(window.location.host)
  ? window.location.origin
  : FLASK_BACKEND_ORIGIN;

const resultsMessage = document.getElementById("results-message");
const resultsRole = document.getElementById("results-role");
const resultsScorePanel = document.getElementById("results-score-panel");
const resultsScoreRing = document.getElementById("results-score-ring");
const resultsScoreValue = document.getElementById("results-score-value");
const resultsScoreBarFill = document.getElementById("results-score-bar-fill");
const resultsDashboardMetrics = document.getElementById("results-dashboard-metrics");
const resultsFeedbackList = document.getElementById("results-feedback-list");
const resultsSuggestionsList = document.getElementById("results-suggestions-list");
const resultsFeedbackCount = document.getElementById("results-feedback-count");
const resultsSuggestionsCount = document.getElementById("results-suggestions-count");
const resultsDownloadButton = document.getElementById("results-download-button");

function getFeedbackTone(text) {
  const normalized = String(text || "").toLowerCase();
  const positiveKeywords = ["good job", "great", "strong", "industry-ready"];

  if (positiveKeywords.some((keyword) => normalized.includes(keyword))) {
    return "positive";
  }

  return "issue";
}

function formatCountLabel(count) {
  return `${count} ${count === 1 ? "item" : "items"}`;
}

function buildDashboardMetrics(result, feedbackItems, suggestionItems) {
  const missingSkills = Array.isArray(result.missing_skills) ? result.missing_skills : [];
  const requiredSkillCount = Math.max(Number(result.required_skill_count) || 0, missingSkills.length);
  const coveredSkills = Math.max(0, requiredSkillCount - missingSkills.length);

  return [
    {
      value: `${feedbackItems.length + suggestionItems.length}`,
      label: "Issues detected"
    },
    {
      value: requiredSkillCount ? `${coveredSkills}/${requiredSkillCount}` : "0/0",
      label: "Keyword coverage"
    },
    {
      value: `${missingSkills.length}`,
      label: "Missing core skills"
    }
  ];
}

function renderMetricCards(container, metrics) {
  if (!container) {
    return;
  }

  container.innerHTML = "";
  metrics.forEach((metric) => {
    const card = document.createElement("div");
    card.className = "metric-card";
    card.innerHTML = `<strong>${metric.value}</strong><span>${metric.label}</span>`;
    container.appendChild(card);
  });
}

function applyScorePresentation(score, ringElement, valueElement, barElement) {
  const normalizedScore = Math.max(0, Math.min(Number(score) || 0, 100));

  if (valueElement) {
    valueElement.textContent = `${normalizedScore}`;
  }

  if (barElement) {
    barElement.style.width = `${normalizedScore}%`;
  }

  if (ringElement) {
    ringElement.style.setProperty("--score-angle", `${normalizedScore * 3.6}deg`);
  }
}

function renderList(container, items, toneOverride = "") {
  if (!container) {
    return;
  }

  container.innerHTML = "";

  if (!items.length) {
    const item = document.createElement("li");
    item.className = "feedback-item positive";
    item.textContent = "No items available.";
    container.appendChild(item);
    return;
  }

  items.forEach((text) => {
    const item = document.createElement("li");
    item.className = `feedback-item ${toneOverride || getFeedbackTone(text)}`;
    item.textContent = text;
    container.appendChild(item);
  });
}

if (!storedPayload) {
  window.location.href = "index.html";
} else {
  const parsed = JSON.parse(storedPayload);
  const result = parsed.result || {};
  const feedbackItems = Array.isArray(result.feedback) ? result.feedback : [];
  const suggestionItems = Array.isArray(result.suggestions) ? result.suggestions : [];

  if (resultsMessage) {
    resultsMessage.textContent = result.message || "Resume generated successfully.";
  }

  if (resultsRole) {
    resultsRole.textContent = result.role ? `Selected role: ${result.role}` : "";
  }

  renderList(resultsFeedbackList, feedbackItems);
  renderList(resultsSuggestionsList, suggestionItems, "suggestion");

  if (resultsFeedbackCount) {
    resultsFeedbackCount.textContent = formatCountLabel(feedbackItems.length);
  }

  if (resultsSuggestionsCount) {
    resultsSuggestionsCount.textContent = formatCountLabel(suggestionItems.length);
  }

  if (resultsScorePanel) {
    resultsScorePanel.hidden = false;
    applyScorePresentation(result.score, resultsScoreRing, resultsScoreValue, resultsScoreBarFill);
  }

  renderMetricCards(resultsDashboardMetrics, buildDashboardMetrics(result, feedbackItems, suggestionItems));

  if (resultsDownloadButton && result.file) {
    resultsDownloadButton.hidden = false;
    resultsDownloadButton.addEventListener("click", () => {
      window.open(`${API_BASE_URL}/download?file=${encodeURIComponent(result.file)}`, "_blank");
    });
  }
}
