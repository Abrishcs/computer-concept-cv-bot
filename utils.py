import re
import validators

def validate_phone(phone):
    # Regex for Ethiopian phone numbers: +251, 251, 09..., 07...
    pattern = r'^(\+251|251|0)?([79]\d{8})$'
    match = re.match(pattern, phone.strip())
    if match:
        return f"+251{match.group(2)}"
    return None

def validate_email(email):
    if validators.email(email.strip()):
        return email.strip()
    return None

def validate_gpa(gpa_str):
    try:
        gpa = float(gpa_str.strip())
        if 0.0 <= gpa <= 4.0:
            return gpa
    except ValueError:
        pass
    return None

def clean_input(text):
    if not text:
        return ""
    # Remove excessive whitespace
    return " ".join(text.split())

def check_quality(text, min_lines=2, min_words=10):
    if not text:
        return False, "Please provide some details."

    words = text.split()

    if len(words) < min_words:
        return False, f"Too short! Please write at least {min_words} words."

    return True, ""

def format_cv_preview(data):
    preview = "📋 *Your CV Preview*\n"
    preview += "━━━━━━━━━━━━━━━━━━━━━\n\n"

    # ── Step 1: Basic Info ──
    preview += "👤 *Basic Information*\n"
    preview += f"• Name: {data.get('full_name', 'N/A')}\n"
    preview += f"• Phone: {data.get('phone', 'N/A')}\n"
    preview += f"• Email: {data.get('email', 'N/A')}\n"
    preview += f"• Location: {data.get('city', 'N/A')}\n"
    if data.get('social'):
        preview += f"• Social: {data.get('social')}\n"
    preview += "\n"

    # ── Step 2: Profile ──
    preview += "📝 *Profile*\n"
    preview += f"{data.get('profile', 'N/A')}\n\n"

    # ── Step 3: Education ──
    preview += "🎓 *Education*\n"
    if data.get('university'):
        preview += f"• University: {data.get('university')}\n"
    if data.get('degree'):
        preview += f"• Degree: {data.get('degree')}\n"
    if data.get('edu_year'):
        preview += f"• Year: {data.get('edu_year')}\n"
    if data.get('gpa'):
        preview += f"• GPA: {data.get('gpa')}\n"
    if not any(data.get(k) for k in ['university', 'degree', 'edu_year', 'gpa']):
        # Fallback to combined education field
        preview += f"{data.get('education', 'N/A')}\n"
    preview += "\n"

    # ── Step 4: Skills ──
    preview += "💻 *Technical Skills*\n"
    preview += f"{data.get('skills', 'N/A')}\n\n"
    preview += "🧠 *Soft Skills*\n"
    preview += f"{data.get('soft_skills', 'N/A')}\n\n"

    # ── Step 5: Projects ──
    preview += "🚀 *Projects*\n"
    preview += f"{data.get('projects', 'N/A')}\n\n"

    # ── Step 6: Experience ──
    if data.get('experience'):
        preview += "💼 *Experience*\n"
        preview += f"{data.get('experience')}\n\n"

    # ── Step 7: Certificates ──
    if data.get('certifications'):
        preview += "📜 *Certificates*\n"
        preview += f"{data.get('certifications')}\n\n"

    # ── Step 8: Languages ──
    preview += f"🌐 *Languages*: {data.get('languages', 'N/A')}\n"

    # ── Uploads status ──
    if data.get('photo_file_id'):
        preview += "\n📸 Photo: ✅ Uploaded"
    else:
        preview += "\n📸 Photo: ❌ Not uploaded"

    if data.get('uploaded_document_id'):
        preview += "\n📄 Document: ✅ Uploaded"

    return preview
