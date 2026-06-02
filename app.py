from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from fpdf import FPDF
from PyPDF2 import PdfReader
import os
import re

app = Flask(__name__)
# Allow frontend calls from browser.
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_FILES = {
    "index.html",
    "builder.html",
    "results.html",
    "styles.css",
    "script.js",
    "results.js",
    "template-selection.js"
}

# Action words that make project descriptions stronger.
ACTION_VERBS = ["developed", "built", "implemented", "created", "designed", "optimized"]

# Section keywords used during uploaded-PDF analysis.
SECTION_KEYWORDS = ["skills", "education", "projects"]

# Resume templates available in the UI.
# We keep old keys as aliases so older frontend values still work.
AVAILABLE_TEMPLATES = {
    "classic",
    "modern",
    "fresher",
    "creative",
    "developer"
}
TEMPLATE_ALIASES = {
    "modern professional": "modern",
    "modern": "modern",
    "classic corporate": "classic",
    "classic": "classic",
    "student fresher": "fresher",
    "fresher": "fresher",
    "minimal elegant": "fresher",
    "minimal": "fresher",
    "creative portfolio": "creative",
    "creative designer": "creative",
    "sidebar portfolio": "creative",
    "sidebar": "creative",
    "developer resume": "developer",
    "developer": "developer",
    "skill-focused resume": "modern",
    "skill focused resume": "modern",
    "skill-focused": "modern",
    "compact": "fresher"
}

# Role-based skills used for resume analysis.
ROLE_SKILLS = {
    "Software Developer": ["python", "java", "sql", "data structures", "git", "problem solving"],
    "Web Developer": ["html", "css", "javascript", "responsive design", "bootstrap", "git"],
    "Full Stack Developer": ["html", "css", "javascript", "react", "node.js", "sql"],
    "Data Analyst": ["excel", "sql", "python", "power bi", "data visualization", "statistics"],
    "AI/ML Engineer": ["python", "machine learning", "deep learning", "tensorflow", "pandas", "numpy"],
    "Cybersecurity Analyst": ["network security", "risk assessment", "siem", "incident response", "vulnerability assessment", "linux"],
    "MBA / Finance": ["financial analysis", "budgeting", "forecasting", "reporting", "communication", "ms excel"],
    "Accountant": ["accounting", "tally", "gst", "financial reporting", "bookkeeping", "ms excel"],
    "Banking": ["customer service", "cash handling", "kyc", "compliance", "sales", "communication"],
    "Business Analyst": ["requirements gathering", "excel", "sql", "documentation", "stakeholder management", "data analysis"],
    "Marketing Executive": ["digital marketing", "seo", "social media", "campaign management", "content creation", "communication"],
    "HR Executive": ["recruitment", "employee engagement", "onboarding", "communication", "hr policies", "ms office"],
    "Mechanical Engineer": ["autocad", "solidworks", "manufacturing", "maintenance", "quality control", "problem solving"],
    "Civil Engineer": ["autocad", "site supervision", "estimation", "construction management", "surveying", "quality control"],
    "Electrical Engineer": ["electrical circuits", "autocad", "troubleshooting", "maintenance", "power systems", "safety standards"],
    "Electronics Engineer": ["embedded systems", "circuit design", "microcontrollers", "pcb", "testing", "troubleshooting"],
    "Biotechnology": ["laboratory techniques", "documentation", "data analysis", "research", "quality control", "communication"],
    "Microbiology": ["microbial testing", "laboratory techniques", "documentation", "sample analysis", "research", "quality control"],
    "Research Assistant": ["research", "data collection", "documentation", "literature review", "report writing", "analysis"],
    "Graphic Designer": ["photoshop", "illustrator", "branding", "layout design", "typography", "creativity"],
    "UI/UX Designer": ["wireframing", "figma", "user research", "prototyping", "usability testing", "design systems"],
    "Content Writer": ["content writing", "seo", "editing", "research", "storytelling", "grammar"],
    "Nurse": ["patient care", "vital signs", "medication administration", "communication", "documentation", "empathy"],
    "Pharmacist": ["pharmacology", "dispensing", "inventory management", "patient counseling", "documentation", "compliance"],
    "Medical Assistant": ["patient care", "appointment scheduling", "medical records", "communication", "vital signs", "documentation"]
}

ROLE_FOCUS_AREAS = {
    "Graphic Designer": "portfolio work",
    "UI/UX Designer": "portfolio work",
    "Content Writer": "writing samples",
    "Research Assistant": "research work",
    "Nurse": "clinical experience",
    "Pharmacist": "pharmacy experience",
    "Medical Assistant": "patient-facing experience"
}

DEFAULT_ROLE = "Software Developer"


def clean_text(text):
    """Lowercase + normalize spaces."""
    value = str(text or "").lower()
    return re.sub(r"\s+", " ", value).strip()


def list_to_text(value):
    """Convert dict/list/string into one plain text block."""
    if isinstance(value, list):
        return " ".join(list_to_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(list_to_text(item) for item in value.values())
    return str(value or "")


def split_items(value):
    """Split comma/newline separated values into cleaned list."""
    text = str(value or "")
    parts = re.split(r"[,/\n;|]+", text)
    items = []
    seen = set()

    for part in parts:
        item = part.strip()
        item_key = item.lower()
        if item and item_key not in seen:
            seen.add(item_key)
            items.append(item)
    return items


def get_selected_role(value):
    """Return a supported role name or a safe default."""
    selected_role = str(value or "").strip()
    return selected_role if selected_role in ROLE_SKILLS else DEFAULT_ROLE


def pdf_safe(text):
    """Make text safe for FPDF latin-1 output."""
    value = str(text or "")
    value = value.replace("•", "-").replace("–", "-").replace("—", "-")
    return value.encode("latin-1", "replace").decode("latin-1")


def section_is_weak(value, min_len=20):
    """Check if a section is empty or too short."""
    section_text = clean_text(list_to_text(value))
    return len(section_text) < min_len


def format_education_line(item):
    """
    Format education as:
    MCA - SIT, VTU (2023-2026) | CGPA: 9
    """
    if not isinstance(item, dict):
        return ""

    degree = str(item.get("degree", "")).strip()
    college = str(item.get("collegeName", "")).strip()
    university = str(item.get("university", "")).strip()
    year = str(item.get("yearOfPassing", "")).strip()
    cgpa = str(item.get("cgpa", "")).strip()

    institution = ", ".join([part for part in [college, university] if part])
    line = ""

    if degree:
        line += degree
    if institution:
        line += f" - {institution}" if line else institution
    if year:
        line += f" ({year})"
    if cgpa:
        line += f" | CGPA: {cgpa}"

    return line.strip()


def split_project_points(description, max_points=3):
    """Split project description into short bullet points."""
    raw = str(description or "").replace("\r", "\n")
    parts = re.split(r"[\n.;]+", raw)
    points = [part.strip() for part in parts if part.strip()]
    return points[:max_points]


def ensure_action_verb(point):
    """Ensure bullet starts with action-oriented style."""
    text = str(point or "").strip()
    if not text:
        return ""

    lower = text.lower()
    if any(lower.startswith(verb) for verb in ACTION_VERBS):
        return text

    # If user did not start with action verb, make it stronger.
    return f"Developed {text[0].lower() + text[1:] if len(text) > 1 else text.lower()}"


def write_section_heading(pdf, title):
    """Write section heading with underline."""
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, pdf_safe(title), ln=True)
    y = pdf.get_y()
    pdf.set_draw_color(95, 95, 95)
    pdf.line(10, y, 200, y)
    pdf.ln(4)


def write_bullet_lines(pdf, lines):
    """Write each line as a bullet."""
    pdf.set_font("Arial", "", 11)
    for line in lines:
        pdf.multi_cell(0, 6, pdf_safe(f"- {line}"))


def build_summary(data):
    """
    Create a professional 2-3 line summary.
    Use user summary if provided; otherwise generate a simple one.
    """
    user_summary = str(data.get("summary", "")).strip()
    if user_summary:
        return user_summary

    skills = data.get("skills", {})
    projects = data.get("projects", [])

    skill_pool = []
    if isinstance(skills, dict):
        skill_pool.extend(split_items(skills.get("technical", "")))
        skill_pool.extend(split_items(skills.get("tools", "")))
    else:
        skill_pool.extend(split_items(skills))

    selected_role = get_selected_role(data.get("jobRole"))
    top_skills = ", ".join(skill_pool[:4]) if skill_pool else selected_role.lower()
    project_count = len(projects) if isinstance(projects, list) else 0

    return (
        f"Detail-oriented candidate with hands-on experience in {top_skills}. "
        f"Built {project_count} project(s) with focus on clean implementation, "
        "problem-solving, and practical impact."
    )


def get_resume_template(data):
    """Read template selection safely without breaking older payloads."""
    selected = clean_text(data.get("template", "classic"))
    normalized = TEMPLATE_ALIASES.get(selected, selected)
    return normalized if normalized in AVAILABLE_TEMPLATES else "classic"


def get_contact_parts(email, phone="", linkedin="", github=""):
    """Build header contact details without changing the existing API shape."""
    parts = [str(email).strip()]
    if str(phone).strip():
        parts.append(str(phone).strip())
    if str(linkedin).strip():
        parts.append(str(linkedin).strip())
    elif str(github).strip():
        parts.append(str(github).strip())
    return [part for part in parts if part]


def get_education_lines(education):
    """Collect UG and PG education lines in one place."""
    lines = []
    if isinstance(education, dict):
        for item in [education.get("ug"), education.get("pg")]:
            line = format_education_line(item)
            if line:
                lines.append(line)
    return lines


def get_skill_lines(skills, technical_label="Core Skills"):
    """Format skills consistently for all templates."""
    technical = split_items(skills.get("technical", "")) if isinstance(skills, dict) else split_items(skills)
    tools = split_items(skills.get("tools", "")) if isinstance(skills, dict) else []
    lines = []
    if technical:
        lines.append(f"{technical_label}: {', '.join(technical)}")
    if tools:
        lines.append(f"Tools: {', '.join(tools)}")
    return lines or ["Not provided"]


def write_colored_section_heading(pdf, title, rgb):
    """Template-specific colored heading used by the modern template."""
    red, green, blue = rgb
    pdf.set_text_color(red, green, blue)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, pdf_safe(title), ln=True)
    y = pdf.get_y()
    pdf.set_draw_color(red, green, blue)
    pdf.line(10, y, 200, y)
    pdf.ln(4)
    pdf.set_text_color(0, 0, 0)


def write_filled_section_heading(pdf, title, fill_rgb, text_rgb=(255, 255, 255)):
    """Write a filled heading block for more visual templates."""
    fill_red, fill_green, fill_blue = fill_rgb
    text_red, text_green, text_blue = text_rgb
    pdf.set_fill_color(fill_red, fill_green, fill_blue)
    pdf.set_text_color(text_red, text_green, text_blue)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, pdf_safe(title), ln=True, fill=True)
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)


def get_resume_sections(data):
    """Collect all resume content once so multiple templates can reuse it safely."""
    return {
        "name": data.get("name") or data.get("fullName") or "Your Name",
        "email": data.get("email") or "email@example.com",
        "phone": data.get("phone") or data.get("phoneNumber") or "",
        "linkedin": data.get("linkedin", ""),
        "github": data.get("github", ""),
        "summary": build_summary(data),
        "education": data.get("education", {}),
        "skills": data.get("skills", {}),
        "projects": data.get("projects", []),
        "certifications": data.get("certifications", ""),
        "achievements": data.get("achievements", "")
    }


def write_project_entries(pdf, projects, max_points=3, title_size=11):
    """Write project titles, bullet points, and technologies in a shared format."""
    if isinstance(projects, list) and projects:
        for project in projects:
            if not isinstance(project, dict):
                continue
            title = str(project.get("title", "")).strip() or "Project"
            description = str(project.get("description", "")).strip()
            technologies = str(project.get("technologies", "")).strip()
            pdf.set_font("Arial", "B", title_size)
            pdf.multi_cell(0, 7, pdf_safe(title))

            points = split_project_points(description, max_points=max_points)
            polished_points = [ensure_action_verb(point) for point in points]
            write_bullet_lines(pdf, polished_points or ["Developed and delivered a practical solution."])

            if technologies:
                write_bullet_lines(pdf, [f"Technologies: {technologies}"])
            pdf.ln(2)
    else:
        write_bullet_lines(pdf, ["Not provided"])


def get_keyword_matches(text, keywords):
    """Return keywords found in text using simple matching."""
    processed = clean_text(text)
    return [keyword for keyword in keywords if keyword in processed]


def calculate_structure_score(text):
    """Give up to 10 marks for basic resume completeness."""
    processed = clean_text(text)
    score = 0

    section_matches = get_keyword_matches(processed, SECTION_KEYWORDS)
    score += min(len(section_matches), 3) * 2

    if len(processed) >= 180:
        score += 2
    if len(processed) >= 320:
        score += 2

    return min(score, 10)


def find_best_matching_role(processed_text):
    """Find which role the resume content most closely matches."""
    best_role = DEFAULT_ROLE
    best_matches = []

    for role_name, role_skills in ROLE_SKILLS.items():
        matches = get_keyword_matches(processed_text, role_skills)
        if len(matches) > len(best_matches):
            best_role = role_name
            best_matches = matches

    return best_role, best_matches


def calculate_resume_score(text, required_skills, role, project_text=""):
    """Score a resume out of 100 with role-aware and context-aware logic."""
    processed = clean_text(text)
    project_processed = clean_text(project_text or text)
    selected_role = get_selected_role(role)

    selected_matches = get_keyword_matches(processed, required_skills)
    selected_ratio = len(selected_matches) / max(len(required_skills), 1)

    best_role, best_role_matches = find_best_matching_role(processed)
    best_ratio = len(best_role_matches) / max(len(ROLE_SKILLS.get(best_role, [])), 1)

    # Role relevance focuses on how well the content matches the chosen role
    # compared with other roles in the system.
    role_alignment_ratio = min(selected_ratio, selected_ratio / max(best_ratio, 0.01))
    role_relevance_score = int(40 * min(role_alignment_ratio, 1))

    # Relevant skills score looks only at selected-role skills.
    skills_score = int(30 * min(selected_ratio, 1))

    # Relevant projects/content score checks whether project content supports the role.
    project_matches = get_keyword_matches(project_processed, required_skills)
    action_matches = get_keyword_matches(project_processed, ACTION_VERBS)
    project_ratio = len(project_matches) / max(len(required_skills), 1)
    project_support_ratio = min(project_ratio + (0.15 if action_matches else 0), 1)
    projects_score = int(20 * project_support_ratio)

    structure_score = calculate_structure_score(processed)

    mismatch_detected = (
        len(selected_matches) <= 1
        and len(best_role_matches) >= 2
        and best_role != selected_role
    ) or (
        selected_ratio < 0.34
        and best_ratio > selected_ratio
        and best_role != selected_role
    )

    total_score = role_relevance_score + skills_score + projects_score + structure_score

    if mismatch_detected:
        total_score = min(total_score, 45)

    return {
        "score": min(total_score, 100),
        "role_relevance_score": role_relevance_score,
        "skills_score": skills_score,
        "projects_score": projects_score,
        "structure_score": structure_score,
        "selected_matches": selected_matches,
        "best_matching_role": best_role,
        "best_role_matches": best_role_matches,
        "mismatch_detected": mismatch_detected
    }


def build_role_based_analysis(text, role, existing_feedback, project_text=""):
    """Extend feedback with role-aware score, missing skills, and suggestions."""
    processed = clean_text(text)
    selected_role = get_selected_role(role)
    required_skills = ROLE_SKILLS.get(selected_role, ROLE_SKILLS[DEFAULT_ROLE])
    missing_skills = [skill for skill in required_skills if skill not in processed]
    focus_area = ROLE_FOCUS_AREAS.get(selected_role, "projects or experience")
    scoring = calculate_resume_score(processed, required_skills, selected_role, project_text=project_text)
    feedback = list(existing_feedback)
    suggestions = []
    mismatch_message = "Resume content does not strongly match the selected role."

    if scoring["mismatch_detected"]:
        if mismatch_message not in feedback:
            feedback.insert(0, mismatch_message)
        better_role_message = f"Your resume looks closer to {scoring['best_matching_role']} than {selected_role}."
        if scoring["best_matching_role"] != selected_role and better_role_message not in feedback:
            feedback.append(
                better_role_message
            )
        suggestions.append(f"Consider adding {selected_role.lower()}-related skills and experience.")

    if "skills" not in processed:
        suggestions.append(f"Add a dedicated Skills section for {selected_role} keywords and strengths.")
    if "education" not in processed:
        suggestions.append("Add an Education section with degree, institution, year, and score.")
    if "projects" not in processed:
        suggestions.append(f"Add a section for {focus_area} with clear outcomes and responsibilities.")
    if not any(verb in processed for verb in ACTION_VERBS):
        suggestions.append("Start your points with action verbs like Developed, Managed, Created, or Improved.")
    if missing_skills:
        top_missing = ", ".join(missing_skills[:3])
        suggestions.append(
            f"If you have used them, mention role-relevant skills for {selected_role} such as {top_missing}."
        )
        if scoring["mismatch_detected"] and selected_role in {"Nurse", "Pharmacist", "Medical Assistant"}:
            suggestions.append("Consider adding healthcare-related skills and experience.")
    if len(processed) < 180:
        suggestions.append("Add more specific detail to make the resume stronger and easier to evaluate.")

    return {
        "feedback": feedback,
        "role": selected_role,
        "required_skills": required_skills,
        "existing_feedback": existing_feedback,
        "score": scoring["score"],
        "missing_skills": missing_skills,
        "required_skill_count": len(required_skills),
        "score_breakdown": {
            "role_relevance": scoring["role_relevance_score"],
            "relevant_skills": scoring["skills_score"],
            "relevant_projects": scoring["projects_score"],
            "structure": scoring["structure_score"]
        },
        "best_matching_role": scoring["best_matching_role"],
        "mismatch_detected": scoring["mismatch_detected"],
        "suggestions": suggestions[:4]
    }


def generate_resume_pdf_modern(data):
    """Generate the Modern Professional template."""
    sections = get_resume_sections(data)
    name = sections["name"]
    email = sections["email"]
    phone = sections["phone"]
    linkedin = sections["linkedin"]
    github = sections["github"]
    summary = sections["summary"]
    education = sections["education"]
    skills = sections["skills"]
    projects = sections["projects"]
    certifications = sections["certifications"]
    achievements = sections["achievements"]

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    accent_color = (31, 78, 121)
    pdf.set_fill_color(24, 43, 72)
    pdf.rect(0, 0, 210, 38, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 16, pdf_safe(name), ln=True, align="C")

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, pdf_safe(" | ".join(get_contact_parts(email, phone, linkedin, github))), ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    # Modern Professional: colored headings with clean spacing.
    write_colored_section_heading(pdf, "Professional Summary", accent_color)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, pdf_safe(summary))
    pdf.ln(6)

    write_colored_section_heading(pdf, "Core Skills", accent_color)
    write_bullet_lines(pdf, get_skill_lines(skills, technical_label="Technical Skills"))
    pdf.ln(4)

    write_colored_section_heading(pdf, "Education", accent_color)
    write_bullet_lines(pdf, get_education_lines(education) or ["Not provided"])
    pdf.ln(4)

    write_colored_section_heading(pdf, "Projects", accent_color)
    write_project_entries(pdf, projects, max_points=3, title_size=12)

    cert_items = split_items(certifications)
    if cert_items:
        pdf.ln(3)
        write_colored_section_heading(pdf, "Certifications", accent_color)
        write_bullet_lines(pdf, cert_items)

    achievement_items = split_items(achievements)
    if achievement_items:
        pdf.ln(3)
        write_colored_section_heading(pdf, "Achievements", accent_color)
        write_bullet_lines(pdf, achievement_items)

    file_name = "resume.pdf"
    file_path = os.path.join(os.getcwd(), file_name)
    pdf.output(file_path)
    return file_name


def generate_resume_pdf_compact(data):
    """Generate the Student Fresher template while keeping old fallback support."""
    sections = get_resume_sections(data)
    name = sections["name"]
    email = sections["email"]
    phone = sections["phone"]
    linkedin = sections["linkedin"]
    github = sections["github"]
    summary = sections["summary"]
    education = sections["education"]
    skills = sections["skills"]
    projects = sections["projects"]
    certifications = sections["certifications"]
    achievements = sections["achievements"]

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    # Student Fresher: clean layout with extra emphasis on education and projects.
    pdf.set_fill_color(237, 244, 255)
    pdf.rect(10, 10, 190, 26, "F")
    pdf.set_text_color(24, 43, 72)
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 12, pdf_safe(name), ln=True, align="C")
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 5, pdf_safe(" | ".join(get_contact_parts(email, phone, linkedin, github))), align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Professional Summary", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 5, pdf_safe(summary))
    pdf.ln(4)

    pdf.set_fill_color(245, 248, 255)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Education", ln=True, fill=True)
    pdf.set_font("Arial", "", 11)
    for line in get_education_lines(education) or ["Not provided"]:
        pdf.multi_cell(0, 5, pdf_safe(line))
        pdf.ln(1)
    pdf.ln(3)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Skills & Competencies", ln=True, fill=True)
    pdf.set_font("Arial", "", 11)
    for line in get_skill_lines(skills, technical_label="Technical Skills"):
        pdf.multi_cell(0, 5, pdf_safe(line))
    pdf.ln(3)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Academic Projects", ln=True, fill=True)
    pdf.set_font("Arial", "", 11)
    write_project_entries(pdf, projects, max_points=3, title_size=11)

    cert_items = split_items(certifications)
    if cert_items:
        pdf.ln(3)
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 8, "Certifications", ln=True, fill=True)
        pdf.set_font("Arial", "", 11)
        write_bullet_lines(pdf, cert_items)

    achievement_items = split_items(achievements)
    if achievement_items:
        pdf.ln(3)
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 8, "Achievements", ln=True, fill=True)
        pdf.set_font("Arial", "", 11)
        write_bullet_lines(pdf, achievement_items)

    file_name = "resume.pdf"
    file_path = os.path.join(os.getcwd(), file_name)
    pdf.output(file_path)
    return file_name


def generate_resume_pdf_creative_portfolio(data):
    """Generate the Creative Portfolio template with sidebar layout."""
    sections = get_resume_sections(data)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    # Creative sidebar with contact info and skills
    pdf.set_fill_color(27, 38, 59)
    pdf.rect(0, 0, 60, 297, "F")
    pdf.set_xy(8, 14)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 18)
    pdf.multi_cell(44, 8, pdf_safe(sections["name"]))
    pdf.set_font("Arial", "", 9)
    pdf.ln(2)
    pdf.multi_cell(44, 5, pdf_safe("\n".join(get_contact_parts(
        sections["email"], sections["phone"], sections["linkedin"], sections["github"]
    ))))
    pdf.ln(6)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(44, 6, "Skills", ln=True)
    pdf.set_font("Arial", "", 9)
    for line in get_skill_lines(sections["skills"], technical_label="Core Skills"):
        pdf.multi_cell(44, 5, pdf_safe(line))
        pdf.ln(1)

    # Main content area with creative styling
    pdf.set_xy(68, 16)
    pdf.set_text_color(0, 0, 0)
    write_colored_section_heading(pdf, "Profile", (124, 26, 74))
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(132, 5, pdf_safe(sections["summary"]))
    pdf.ln(2)

    write_colored_section_heading(pdf, "Projects", (234, 88, 12))
    write_project_entries(pdf, sections["projects"], max_points=3, title_size=11)

    write_colored_section_heading(pdf, "Education", (14, 116, 144))
    write_bullet_lines(pdf, get_education_lines(sections["education"]) or ["Not provided"])

    cert_items = split_items(sections["certifications"])
    if cert_items:
        write_colored_section_heading(pdf, "Certifications", (89, 86, 233))
        write_bullet_lines(pdf, cert_items)

    achievement_items = split_items(sections["achievements"])
    if achievement_items:
        write_colored_section_heading(pdf, "Achievements", (192, 38, 211))
        write_bullet_lines(pdf, achievement_items)

    return save_resume_pdf(pdf)


def generate_resume_pdf_developer(data):
    """Generate the Developer Resume template."""
    sections = get_resume_sections(data)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 30, "F")
    pdf.set_text_color(240, 249, 255)
    pdf.set_font("Arial", "B", 21)
    pdf.cell(0, 13, pdf_safe(sections["name"]), ln=True, align="C")
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, pdf_safe(" | ".join(get_contact_parts(
        sections["email"], sections["phone"], sections["linkedin"], sections["github"]
    ))), ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    write_filled_section_heading(pdf, "Tech Summary", (15, 23, 42))
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 5, pdf_safe(sections["summary"]))

    write_filled_section_heading(pdf, "Skills", (30, 41, 59))
    write_bullet_lines(pdf, get_skill_lines(sections["skills"], technical_label="Languages & Frameworks"))

    write_filled_section_heading(pdf, "Projects", (51, 65, 85))
    write_project_entries(pdf, sections["projects"], max_points=3, title_size=10)

    write_filled_section_heading(pdf, "Education", (71, 85, 105))
    write_bullet_lines(pdf, get_education_lines(sections["education"]) or ["Not provided"])

    cert_items = split_items(sections["certifications"])
    if cert_items:
        write_filled_section_heading(pdf, "Certifications", (100, 116, 139))
        write_bullet_lines(pdf, cert_items)

    achievement_items = split_items(sections["achievements"])
    if achievement_items:
        write_filled_section_heading(pdf, "Achievements", (120, 130, 150))
        write_bullet_lines(pdf, achievement_items)

    return save_resume_pdf(pdf)


def save_resume_pdf(pdf):
    """Save generated PDF to the existing filename used by current routes."""
    file_name = "resume.pdf"
    file_path = os.path.join(os.getcwd(), file_name)
    pdf.output(file_path)
    return file_name


def generate_resume_pdf(data):
    """Generate a clean, professional resume PDF."""
    template_name = get_resume_template(data)
    if template_name == "modern":
        return generate_resume_pdf_modern(data)
    if template_name == "fresher":
        return generate_resume_pdf_compact(data)
    if template_name == "creative":
        return generate_resume_pdf_creative_portfolio(data)
    if template_name == "developer":
        return generate_resume_pdf_developer(data)

    name = data.get("name") or data.get("fullName") or "Your Name"
    email = data.get("email") or "email@example.com"
    phone = data.get("phone") or data.get("phoneNumber") or ""
    linkedin = data.get("linkedin", "")
    github = data.get("github", "")
    summary = build_summary(data)
    education = data.get("education", {})
    skills = data.get("skills", {})
    projects = data.get("projects", [])
    certifications = data.get("certifications", "")
    achievements = data.get("achievements", "")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Classic Corporate: black-and-white professional layout.
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 14, pdf_safe(name), ln=True, align="C")

    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, pdf_safe(" | ".join(get_contact_parts(email, phone, linkedin, github))), align="C")
    pdf.ln(4)

    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    # Professional Summary
    write_section_heading(pdf, "Professional Summary")
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, pdf_safe(summary))
    pdf.ln(6)

    # Skills
    write_section_heading(pdf, "Skills")
    write_bullet_lines(pdf, get_skill_lines(skills, technical_label="Core Competencies"))
    pdf.ln(4)

    # Education
    write_section_heading(pdf, "Education")
    education_lines = get_education_lines(education)
    if education_lines:
        for line in education_lines:
            pdf.multi_cell(0, 6, pdf_safe(line))
            pdf.ln(2)
    else:
        pdf.multi_cell(0, 6, "Not provided")
    pdf.ln(4)

    # Projects
    write_section_heading(pdf, "Professional Experience")
    if isinstance(projects, list) and projects:
        for project in projects:
            if not isinstance(project, dict):
                continue

            title = str(project.get("title", "")).strip() or "Project"
            description = str(project.get("description", "")).strip()
            technologies = str(project.get("technologies", "")).strip()

            pdf.set_font("Arial", "B", 12)
            pdf.multi_cell(0, 7, pdf_safe(title))

            project_points = split_project_points(description, max_points=3)
            if project_points:
                polished_points = [ensure_action_verb(point) for point in project_points]
                write_bullet_lines(pdf, polished_points)
            else:
                write_bullet_lines(pdf, ["Developed and delivered a practical solution."])

            if technologies:
                write_bullet_lines(pdf, [f"Technologies: {technologies}"])

            pdf.ln(3)
    else:
        pdf.multi_cell(0, 6, "Not provided")

    # Optional sections
    cert_items = split_items(certifications)
    if cert_items:
        pdf.ln(2)
        write_section_heading(pdf, "Certifications")
        write_bullet_lines(pdf, cert_items)

    achievement_items = split_items(achievements)
    if achievement_items:
        pdf.ln(2)
        write_section_heading(pdf, "Achievements")
        write_bullet_lines(pdf, achievement_items)

    return save_resume_pdf(pdf)


def build_feedback_from_data(data):
    """Generate clear and actionable feedback for manual form submission."""
    selected_role = get_selected_role(data.get("jobRole"))
    combined_text = clean_text(
        " ".join([
            list_to_text(data.get("name", "")),
            list_to_text(data.get("email", "")),
            list_to_text(data.get("phone", "")),
            list_to_text(data.get("skills", "")),
            list_to_text(data.get("education", "")),
            list_to_text(data.get("projects", "")),
            list_to_text(data.get("certifications", "")),
            list_to_text(data.get("achievements", ""))
        ])
    )

    feedback = []

    # 1) Missing role-based skills
    required_skills = ROLE_SKILLS.get(selected_role, ROLE_SKILLS[DEFAULT_ROLE])
    missing_skills = [skill for skill in required_skills if skill not in combined_text]
    if missing_skills:
        feedback.append(
            f"For {selected_role}, consider adding these relevant skills if you have them: "
            + ", ".join(missing_skills[:4]) + "."
        )

    # 2) Weak core sections
    weak_sections = []
    if section_is_weak(data.get("skills", "")):
        weak_sections.append("skills")
    if section_is_weak(data.get("education", "")):
        weak_sections.append("education")
    if section_is_weak(data.get("projects", "")):
        weak_sections.append("projects")

    if weak_sections:
        feedback.append(
            "These sections look weak or too short: "
            + ", ".join(weak_sections)
            + ". Add more specific details."
        )

    # 3) Project description quality
    projects = data.get("projects", [])
    project_descriptions = []
    project_technologies = []
    if isinstance(projects, list):
        for item in projects:
            if isinstance(item, dict):
                project_descriptions.append(str(item.get("description", "")))
                project_technologies.append(str(item.get("technologies", "")))

    all_project_text = clean_text(" ".join(project_descriptions))
    role_project_text = clean_text(" ".join(project_descriptions + project_technologies))
    has_action = any(verb in all_project_text for verb in ACTION_VERBS)
    if not has_action:
        feedback.append(
            "Use stronger action verbs in your points, for example: Developed, Managed, Created, Improved."
        )

    if project_descriptions and all(len(clean_text(desc)) < 40 for desc in project_descriptions):
        feedback.append(
            "Project descriptions are too short. Add 2-3 impact-focused bullet points for each project."
        )

    if not project_descriptions:
        feedback.append("Add at least one project with clear outcome and technologies used.")

    scoring = calculate_resume_score(combined_text, required_skills, selected_role, project_text=role_project_text)
    if scoring["mismatch_detected"]:
        feedback.insert(0, "Resume content does not strongly match the selected role.")
        feedback.append(
            f"Consider adding {selected_role.lower()}-related skills, projects, and experience."
        )

    if not feedback:
        feedback.append(f"Great job. Your {selected_role} resume looks strong and role-ready.")

    return feedback


def extract_text_from_pdf(file_obj):
    """Extract text from uploaded PDF file."""
    reader = PdfReader(file_obj)
    text_parts = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return " ".join(text_parts)


def build_feedback_from_uploaded_text(text, role):
    """Generate feedback from uploaded PDF content."""
    processed = clean_text(text)
    selected_role = get_selected_role(role)
    required_skills = ROLE_SKILLS.get(selected_role, ROLE_SKILLS[DEFAULT_ROLE])
    focus_area = ROLE_FOCUS_AREAS.get(selected_role, "projects or experience")
    feedback = []

    # Missing role-based skills
    missing_skills = [skill for skill in required_skills if skill not in processed]
    if missing_skills:
        feedback.append(
            f"Missing important {selected_role} skills (if relevant): " + ", ".join(missing_skills[:4]) + "."
        )

    # Missing section keywords
    weak_sections = []
    if "skills" not in processed:
        weak_sections.append("skills")
    if "education" not in processed:
        weak_sections.append("education")
    if "projects" not in processed:
        weak_sections.append(focus_area)
    if weak_sections:
        feedback.append("These sections look missing or weak: " + ", ".join(weak_sections) + ".")

    # Action verbs in projects/experience
    if not any(verb in processed for verb in ACTION_VERBS):
        feedback.append(
            "Use action verbs like Developed, Managed, Created, or Improved in your points."
        )

    if len(processed) < 120:
        feedback.append("Very little readable text found. Upload a text-based PDF resume.")

    scoring = calculate_resume_score(processed, required_skills, selected_role, project_text=processed)
    if scoring["mismatch_detected"]:
        feedback.insert(0, "Resume content does not strongly match the selected role.")
        feedback.append(
            f"Consider adding {selected_role.lower()}-related skills and experience."
        )

    if not feedback:
        feedback.append(f"Good job. Your uploaded resume matches the {selected_role} role quite well.")

    return feedback


@app.route("/", methods=["GET"])
def index_page():
    """Serve the template selection page."""
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/builder", methods=["GET"])
def builder_page():
    """Serve the resume builder page."""
    return send_from_directory(BASE_DIR, "builder.html")


@app.route("/results", methods=["GET"])
def results_page():
    """Serve the generated resume results page."""
    return send_from_directory(BASE_DIR, "results.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    """Small endpoint for checking that Flask is running."""
    return jsonify({"status": "ok"}), 200


@app.route("/<path:file_name>", methods=["GET"])
def frontend_asset(file_name):
    """Serve whitelisted frontend files from the project root."""
    safe_file = os.path.basename(file_name)

    if safe_file not in FRONTEND_FILES or safe_file != file_name:
        return jsonify({"message": "File not found."}), 404

    return send_from_directory(BASE_DIR, safe_file)


@app.route("/download", methods=["GET"])
def download_resume():
    """Download generated resume PDF."""
    requested_file = request.args.get("file", "resume.pdf")
    safe_file = os.path.basename(requested_file)
    file_path = os.path.join(BASE_DIR, safe_file)

    if not os.path.exists(file_path):
        return jsonify({"message": "Requested file not found."}), 404

    return send_file(file_path, as_attachment=True, download_name=safe_file)


@app.route("/analyze", methods=["POST"])
def analyze_uploaded_resume():
    """Analyze uploaded PDF resume."""
    uploaded_file = request.files.get("resume")

    if not uploaded_file:
        return jsonify({
            "message": "No file uploaded. Please upload a PDF resume.",
            "feedback": []
        }), 400

    if not uploaded_file.filename.lower().endswith(".pdf"):
        return jsonify({
            "message": "Invalid file type. Please upload a PDF file.",
            "feedback": []
        }), 400

    selected_role = get_selected_role(request.form.get("jobRole"))

    try:
        extracted_text = extract_text_from_pdf(uploaded_file)
    except Exception:
        return jsonify({
            "message": "Could not read PDF file. Please try another PDF.",
            "feedback": []
        }), 400

    feedback = build_feedback_from_uploaded_text(extracted_text, selected_role)
    enhanced_feedback = build_role_based_analysis(
        extracted_text,
        selected_role,
        feedback,
        project_text=extracted_text
    )
    return jsonify({
        "message": f"Resume analyzed successfully for {enhanced_feedback['role']}",
        "feedback": enhanced_feedback["feedback"],
        "role": enhanced_feedback["role"],
        "required_skills": enhanced_feedback["required_skills"],
        "score": enhanced_feedback["score"],
        "score_breakdown": enhanced_feedback["score_breakdown"],
        "missing_skills": enhanced_feedback["missing_skills"],
        "required_skill_count": enhanced_feedback["required_skill_count"],
        "best_matching_role": enhanced_feedback["best_matching_role"],
        "mismatch_detected": enhanced_feedback["mismatch_detected"],
        "suggestions": enhanced_feedback["suggestions"]
    }), 200


@app.route("/submit", methods=["POST"])
def submit_resume():
    """Accept JSON resume data, generate feedback, and create PDF."""
    data = request.get_json(silent=True) or {}

    # Print payload for debugging/testing.
    print("Received data from frontend:")
    print(data)

    selected_role = get_selected_role(data.get("jobRole"))
    feedback = build_feedback_from_data(data)
    combined_text = " ".join([
        list_to_text(data.get("name", "")),
        list_to_text(data.get("email", "")),
        list_to_text(data.get("phone", "")),
        list_to_text(data.get("skills", "")),
        list_to_text(data.get("education", "")),
        list_to_text(data.get("projects", "")),
        list_to_text(data.get("certifications", "")),
        list_to_text(data.get("achievements", ""))
    ])
    project_text = list_to_text(data.get("projects", ""))
    enhanced_feedback = build_role_based_analysis(
        combined_text,
        selected_role,
        feedback,
        project_text=project_text
    )
    file_name = generate_resume_pdf(data)

    return jsonify({
        "message": f"Resume generated successfully for {enhanced_feedback['role']}",
        "feedback": enhanced_feedback["feedback"],
        "role": enhanced_feedback["role"],
        "required_skills": enhanced_feedback["required_skills"],
        "existing_feedback": enhanced_feedback["existing_feedback"],
        "score": enhanced_feedback["score"],
        "score_breakdown": enhanced_feedback["score_breakdown"],
        "missing_skills": enhanced_feedback["missing_skills"],
        "required_skill_count": enhanced_feedback["required_skill_count"],
        "best_matching_role": enhanced_feedback["best_matching_role"],
        "mismatch_detected": enhanced_feedback["mismatch_detected"],
        "suggestions": enhanced_feedback["suggestions"],
        "file": file_name
    }), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
