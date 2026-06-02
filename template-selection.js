const TEMPLATE_STORAGE_KEY = "resumeBuilderSelectedTemplate";
const templateSelectionCards = document.querySelectorAll(".template-card");
const selectedTemplateBadge = document.getElementById("selected-template-badge");

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

function getStoredTemplate() {
  const storedTemplate = localStorage.getItem(TEMPLATE_STORAGE_KEY);
  const normalized = TEMPLATE_ALIAS_MAP[storedTemplate] || storedTemplate;
  return TEMPLATE_NAME_MAP[normalized] ? normalized : "classic";
}

function syncTemplateSelection(selectedTemplate) {
  templateSelectionCards.forEach((card) => {
    const isActive = card.dataset.templateValue === selectedTemplate;
    card.classList.toggle("active", isActive);
  });

  if (selectedTemplateBadge) {
    selectedTemplateBadge.textContent = TEMPLATE_NAME_MAP[selectedTemplate] || "Classic Corporate";
  }
}

function applyTemplateSelection(templateValue) {
  const selectedTemplate = TEMPLATE_NAME_MAP[templateValue] ? templateValue : "classic";
  localStorage.setItem(TEMPLATE_STORAGE_KEY, selectedTemplate);
  syncTemplateSelection(selectedTemplate);
  window.location.href = "builder.html";
}

const initialTemplate = getStoredTemplate();
syncTemplateSelection(initialTemplate);

templateSelectionCards.forEach((card) => {
  card.addEventListener("click", (event) => {
    if (event.target instanceof HTMLElement && event.target.closest(".template-use-button")) {
      applyTemplateSelection(card.dataset.templateValue || "classic");
      return;
    }

    syncTemplateSelection(card.dataset.templateValue || "classic");
  });
});
