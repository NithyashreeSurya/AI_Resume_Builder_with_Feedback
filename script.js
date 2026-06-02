const modeTabs = document.querySelectorAll(".mode-tab");
const panels = document.querySelectorAll(".content-panel");
const uploadInput = document.getElementById("resume-upload");
const uploadJobRole = document.getElementById("upload-job-role");
const uploadZone = document.querySelector(".upload-zone");
const filePreview = document.getElementById("file-preview");
const fileName = document.getElementById("file-name");
const fileMeta = document.getElementById("file-meta");
const analyzeUploadResumeButton = document.getElementById("analyze-upload-resume");
const uploadFeedbackSection = document.getElementById("upload-feedback-section");
const uploadFeedbackMessage = document.getElementById("upload-feedback-message");
const uploadFeedbackList = document.getElementById("upload-feedback-list");
const uploadSuggestionsList = document.getElementById("upload-suggestions-list");
const uploadScorePanel = document.getElementById("upload-score-panel");
const uploadScoreValue = document.getElementById("upload-score-value");
const uploadScoreBarFill = document.getElementById("upload-score-bar-fill");
const uploadScoreRing = document.getElementById("upload-score-ring");
const uploadDashboardMetrics = document.getElementById("upload-dashboard-metrics");
const uploadFeedbackCount = document.getElementById("upload-feedback-count");
const uploadSuggestionsCount = document.getElementById("upload-suggestions-count");
const feedbackSection = document.getElementById("feedback-section");
const feedbackMessage = document.getElementById("feedback-message");
const feedbackList = document.getElementById("feedback-list");
const suggestionsList = document.getElementById("suggestions-list");
const scorePanel = document.getElementById("score-panel");
const scoreValue = document.getElementById("score-value");
const scoreBarFill = document.getElementById("score-bar-fill");
const scoreRing = document.getElementById("score-ring");
const dashboardMetrics = document.getElementById("dashboard-metrics");
const feedbackCount = document.getElementById("feedback-count");
const suggestionsCount = document.getElementById("suggestions-count");
const downloadResumeButton = document.getElementById("download-resume");
const resumeForm = document.getElementById("resume-form");
const selectedTemplateName = document.getElementById("selected-template-name");
const hasPgCheckbox = document.getElementById("has-pg");
const pgSection = document.getElementById("pg-education-section");
const pgFields = document.querySelectorAll("[data-pg-field]");
const formSteps = document.querySelectorAll(".form-step");
const prevStepButton = document.getElementById("prev-step");
const nextStepButton = document.getElementById("next-step");
const analyzeResumeButton = document.getElementById("analyze-resume");
const stepCount = document.getElementById("step-count");
const stepTitle = document.getElementById("step-title");
const stepDescription = document.getElementById("step-description");
const stepTrackFill = document.getElementById("step-track-fill");

let currentStepIndex = 0;
const FLASK_BACKEND_ORIGIN = "http://127.0.0.1:5000";
const API_BASE_URL = ["127.0.0.1:5000", "localhost:5000"].includes(window.location.host)
  ? window.location.origin
  : FLASK_BACKEND_ORIGIN;
const TEMPLATE_STORAGE_KEY = "resumeBuilderSelectedTemplate";
const TEMPLATE_NAME_MAP = {
  modern: "Modern Professional",
  classic: "Classic Corporate",
  fresher: "Student Fresher",
  creative: "Creative Portfolio",
  developer: "Developer Resume"
};

const TEMPLATE_ALIAS_MAP = {
  "minimal elegant": "fresher",
  "minimal": "fresher",
  "skill-focused resume": "modern",
  "skill focused resume": "modern",
  "skill-focused": "modern",
  "sidebar portfolio": "creative",
  "sidebar": "creative",
  "compact": "fresher"
};

function collectResumeData() {
  return {
    name: resumeForm?.elements.fullName?.value.trim() || "",
    email: resumeForm?.elements.email?.value.trim() || "",
    phone: resumeForm?.elements.phoneNumber?.value.trim() || "",
    linkedin: resumeForm?.elements.linkedin?.value.trim() || "",
    github: resumeForm?.elements.github?.value.trim() || "",
    jobRole: resumeForm?.elements.jobRole?.value || "",
    template: resumeForm?.elements.resumeTemplate?.value || "classic",
    skills: {
      technical: resumeForm?.elements.technicalSkills?.value.trim() || "",
      tools: resumeForm?.elements.tools?.value.trim() || ""
    },
    education: {
      ug: {
        degree: resumeForm?.elements.ugDegree?.value.trim() || "",
        collegeName: resumeForm?.elements.ugCollegeName?.value.trim() || "",
        university: resumeForm?.elements.ugUniversity?.value.trim() || "",
        yearOfPassing: resumeForm?.elements.ugYearOfPassing?.value.trim() || "",
        cgpa: resumeForm?.elements.ugCgpa?.value.trim() || ""
      },
      pg: hasPgCheckbox?.checked
        ? {
            degree: resumeForm?.elements.pgDegree?.value.trim() || "",
            collegeName: resumeForm?.elements.pgCollegeName?.value.trim() || "",
            university: resumeForm?.elements.pgUniversity?.value.trim() || "",
            yearOfPassing: resumeForm?.elements.pgYearOfPassing?.value.trim() || "",
            cgpa: resumeForm?.elements.pgCgpa?.value.trim() || ""
          }
        : null
    },
    projects: [
      {
        title: resumeForm?.elements.projectTitle?.value.trim() || "",
        description: resumeForm?.elements.projectDescription?.value.trim() || "",
        technologies: resumeForm?.elements.projectTechnologies?.value.trim() || ""
      }
    ],
    certifications: resumeForm?.elements.certifications?.value.trim() || "",
    achievements: resumeForm?.elements.achievements?.value.trim() || ""
  };
}

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

function renderFormFeedback(result) {
  if (!feedbackSection || !feedbackMessage || !feedbackList) {
    alert(result.message || "Resume generated successfully.");
    return;
  }

  feedbackSection.hidden = false;
  feedbackMessage.textContent = result.message || "Resume analysis completed.";
  feedbackList.innerHTML = "";

  const items = Array.isArray(result.feedback) ? result.feedback : [];
  items.forEach((point) => {
    const item = document.createElement("li");
    item.className = `feedback-item ${getFeedbackTone(point)}`;
    item.textContent = point;
    feedbackList.appendChild(item);
  });

  if (suggestionsList) {
    suggestionsList.innerHTML = "";
    const suggestions = Array.isArray(result.suggestions) ? result.suggestions : [];
    suggestions.forEach((point) => {
      const item = document.createElement("li");
      item.className = "feedback-item suggestion";
      item.textContent = point;
      suggestionsList.appendChild(item);
    });

    if (suggestionsCount) {
      suggestionsCount.textContent = formatCountLabel(suggestions.length);
    }
  }

  if (feedbackCount) {
    feedbackCount.textContent = formatCountLabel(items.length);
  }

  if (scorePanel && scoreValue && scoreBarFill) {
    scorePanel.hidden = false;
    applyScorePresentation(result.score, scoreRing, scoreValue, scoreBarFill);
  }

  renderMetricCards(dashboardMetrics, buildDashboardMetrics(result, items, Array.isArray(result.suggestions) ? result.suggestions : []));

  if (downloadResumeButton && result.file) {
    downloadResumeButton.hidden = false;
    downloadResumeButton.onclick = () => {
      window.open(`${API_BASE_URL}/download?file=${encodeURIComponent(result.file)}`, "_blank");
    };
  }
}

function renderUploadFeedback(result) {
  if (!uploadFeedbackSection || !uploadFeedbackMessage || !uploadFeedbackList) {
    return;
  }

  uploadFeedbackSection.hidden = false;
  uploadFeedbackMessage.textContent = result.message || "Resume analysis completed.";
  uploadFeedbackList.innerHTML = "";

  const items = Array.isArray(result.feedback) ? result.feedback : [];
  if (!items.length) {
    const item = document.createElement("li");
    item.className = "feedback-item positive";
    item.textContent = "No feedback items received from backend.";
    uploadFeedbackList.appendChild(item);
  } else {
    items.forEach((point) => {
      const item = document.createElement("li");
      item.className = `feedback-item ${getFeedbackTone(point)}`;
      item.textContent = point;
      uploadFeedbackList.appendChild(item);
    });
  }

  if (uploadSuggestionsList) {
    uploadSuggestionsList.innerHTML = "";
    const suggestions = Array.isArray(result.suggestions) ? result.suggestions : [];
    suggestions.forEach((point) => {
      const item = document.createElement("li");
      item.className = "feedback-item suggestion";
      item.textContent = point;
      uploadSuggestionsList.appendChild(item);
    });

    if (uploadSuggestionsCount) {
      uploadSuggestionsCount.textContent = formatCountLabel(suggestions.length);
    }
  }

  if (uploadFeedbackCount) {
    uploadFeedbackCount.textContent = formatCountLabel(items.length);
  }

  if (uploadScorePanel && uploadScoreValue && uploadScoreBarFill) {
    uploadScorePanel.hidden = false;
    applyScorePresentation(result.score, uploadScoreRing, uploadScoreValue, uploadScoreBarFill);
  }

  renderMetricCards(uploadDashboardMetrics, buildDashboardMetrics(result, items, Array.isArray(result.suggestions) ? result.suggestions : []));
}

async function submitResumeData() {
  const payload = collectResumeData();

  try {
    const response = await fetch(`${API_BASE_URL}/submit`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.message || `Server returned ${response.status}`);
    }

    sessionStorage.setItem(
      "resumeBuilderManualResult",
      JSON.stringify({
        result,
        submittedAt: new Date().toISOString()
      })
    );
    window.location.href = "results.html";
  } catch (error) {
    console.error("Error submitting resume data:", error);
    alert("Could not submit data. Make sure Flask backend is running on port 5000.");
  }
}

async function analyzeUploadedResume() {
  const file = uploadInput?.files?.[0];

  if (!file) {
    alert("Please select a PDF file first.");
    return;
  }

  const formData = new FormData();
  formData.append("resume", file);
  formData.append("jobRole", uploadJobRole?.value || "Software Developer");

  try {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: "POST",
      body: formData
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.message || `Server returned ${response.status}`);
    }

    renderUploadFeedback(result);
  } catch (error) {
    console.error("Error analyzing uploaded resume:", error);
    alert("Could not analyze resume. Make sure Flask backend is running.");
  }
}

function switchMode(targetMode) {
  modeTabs.forEach((tab) => {
    const isActive = tab.dataset.mode === targetMode;
    tab.classList.toggle("active", isActive);
    tab.setAttribute("aria-selected", String(isActive));
  });

  panels.forEach((panel) => {
    const isActive = panel.id === `${targetMode}-panel`;
    panel.classList.toggle("active", isActive);
    panel.hidden = !isActive;
  });
}

function getStoredTemplate() {
  const storedTemplate = localStorage.getItem(TEMPLATE_STORAGE_KEY);
  const normalized = TEMPLATE_ALIAS_MAP[storedTemplate] || storedTemplate;
  return TEMPLATE_NAME_MAP[normalized] ? normalized : "classic";
}

function syncSelectedTemplateUi() {
  const templateField = resumeForm?.elements.resumeTemplate;
  const selectedTemplate = getStoredTemplate();

  if (templateField) {
    templateField.value = selectedTemplate;
  }

  if (selectedTemplateName) {
    selectedTemplateName.textContent = TEMPLATE_NAME_MAP[selectedTemplate] || "Classic Corporate";
  }
}

modeTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    switchMode(tab.dataset.mode);
  });
});

function syncPgSection() {
  if (!hasPgCheckbox || !pgSection) {
    return;
  }

  const showPgSection = hasPgCheckbox.checked;
  pgSection.hidden = !showPgSection;
  hasPgCheckbox.setAttribute("aria-expanded", String(showPgSection));

  pgFields.forEach((field) => {
    field.required = showPgSection;
    field.disabled = !showPgSection;

    if (!showPgSection) {
      field.value = "";
    }
  });
}

function getStepInputs(step) {
  if (!step) {
    return [];
  }

  return [...step.querySelectorAll("input, textarea, select")].filter((field) => !field.disabled);
}

function validateCurrentStep() {
  const currentStep = formSteps[currentStepIndex];
  const stepInputs = getStepInputs(currentStep);

  for (const field of stepInputs) {
    if (!field.checkValidity()) {
      field.reportValidity();
      return false;
    }
  }

  return true;
}

function validateAllSteps() {
  for (let index = 0; index < formSteps.length; index += 1) {
    const step = formSteps[index];
    const stepInputs = getStepInputs(step);

    for (const field of stepInputs) {
      if (!field.checkValidity()) {
        currentStepIndex = index;
        updateStepUi();
        field.reportValidity();
        field.scrollIntoView({ behavior: "smooth", block: "center" });
        return false;
      }
    }
  }

  return true;
}

function updateStepUi() {
  if (!formSteps.length) {
    return;
  }

  formSteps.forEach((step, index) => {
    const isActive = index === currentStepIndex;
    step.classList.toggle("active", isActive);
    step.hidden = !isActive;
  });

  const activeStep = formSteps[currentStepIndex];
  const totalSteps = formSteps.length;

  if (stepCount) {
    stepCount.textContent = `Step ${currentStepIndex + 1} of ${totalSteps}`;
  }

  if (stepTitle) {
    stepTitle.textContent = activeStep.dataset.stepTitle || `Step ${currentStepIndex + 1}`;
  }

  if (stepDescription) {
    stepDescription.textContent = activeStep.dataset.stepDescription || "";
  }

  if (stepTrackFill) {
    stepTrackFill.style.width = `${((currentStepIndex + 1) / totalSteps) * 100}%`;
  }

  if (prevStepButton) {
    prevStepButton.hidden = currentStepIndex === 0;
  }

  const isLastStep = currentStepIndex === totalSteps - 1;

  if (nextStepButton) {
    nextStepButton.hidden = isLastStep;
  }

  if (analyzeResumeButton) {
    analyzeResumeButton.hidden = !isLastStep;
  }
}

function goToStep(nextIndex) {
  if (nextIndex < 0 || nextIndex >= formSteps.length) {
    return;
  }

  currentStepIndex = nextIndex;
  updateStepUi();
  formSteps[currentStepIndex].scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderFile(file) {
  if (!file) {
    filePreview.hidden = true;
    return;
  }

  fileName.textContent = file.name;
  fileMeta.textContent = `${Math.max(1, Math.round(file.size / 1024))} KB • Ready for AI analysis`;
  filePreview.hidden = false;
}

if (uploadInput) {
  uploadInput.addEventListener("change", (event) => {
    renderFile(event.target.files[0]);
    if (uploadFeedbackSection) {
      uploadFeedbackSection.hidden = true;
    }
  });
}

if (hasPgCheckbox) {
  hasPgCheckbox.addEventListener("change", syncPgSection);
  syncPgSection();
}

if (resumeForm?.elements.resumeTemplate) {
  syncSelectedTemplateUi();
}

if (prevStepButton) {
  prevStepButton.addEventListener("click", () => {
    goToStep(currentStepIndex - 1);
  });
}

if (nextStepButton) {
  nextStepButton.addEventListener("click", () => {
    if (!validateCurrentStep()) {
      return;
    }

    goToStep(currentStepIndex + 1);
  });
}

if (analyzeResumeButton) {
  analyzeResumeButton.addEventListener("click", async () => {
    if (!resumeForm || !validateAllSteps()) {
      return;
    }

    await submitResumeData();
  });
}

if (analyzeUploadResumeButton) {
  analyzeUploadResumeButton.addEventListener("click", async () => {
    await analyzeUploadedResume();
  });
}

if (formSteps.length) {
  updateStepUi();
}

if (uploadZone && uploadInput) {
  ["dragenter", "dragover"].forEach((eventName) => {
    uploadZone.addEventListener(eventName, (event) => {
      event.preventDefault();
      uploadZone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    uploadZone.addEventListener(eventName, (event) => {
      event.preventDefault();
      uploadZone.classList.remove("dragover");
    });
  });

  uploadZone.addEventListener("drop", (event) => {
    const [file] = event.dataTransfer.files;
    if (!file) {
      return;
    }

    if (file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")) {
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      uploadInput.files = dataTransfer.files;
      renderFile(file);
    }
  });
}
