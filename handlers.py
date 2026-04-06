import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler
)
from database import Database
from utils import validate_phone, validate_email, validate_gpa, clean_input, check_quality, format_cv_preview

import os
import logging
from dotenv import load_dotenv

load_dotenv()
try:
    ADMIN_ID = int(os.getenv('ADMIN_ID')) if os.getenv('ADMIN_ID') else None
except ValueError:
    ADMIN_ID = None
    logging.error("❌ Invalid ADMIN_ID in .env file. It must be a numeric ID.")

db = Database()
print(f"DEBUG: ADMIN_ID loaded as {ADMIN_ID}")

async def test_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_ID:
        await update.message.reply_text("❌ ADMIN_ID is not set in .env!")
        return
    print(f"DEBUG: Manually triggering test_admin to {ADMIN_ID}...")
    try:
        msg = await context.bot.send_message(chat_id=ADMIN_ID, text="🔔 Test Notification from your CV Bot!")
        print(f"DEBUG: Message sent. Message ID: {msg.message_id}")
        await update.message.reply_text(f"✅ Test message sent to {ADMIN_ID}!\nMessage ID: {msg.message_id}")
    except Exception as e:
        print(f"DEBUG: Failed to send message: {e}")
        await update.message.reply_text(f"❌ Failed to reach {ADMIN_ID}: {e}")

# ─────────────────────────────────────────────
# UI Helpers
# ─────────────────────────────────────────────
def get_nav_markup(step=None):
    """Return a ReplyKeyboardMarkup with 'Back' and 'Cancel' buttons."""
    buttons = [["🔙 Back", "❌ Cancel"]]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=False)

def get_progress_bar(step, total=8):
    """Return a visual progress bar string."""
    filled = "🔵" * step
    empty = "⚪" * (total - step)
    percent = int((step / total) * 100)
    return f"✨ *Section {step}/{total}* | {percent}%\n`{filled}{empty}`"

# ─────────────────────────────────────────────
# States
# ─────────────────────────────────────────────
(
    SELECTING_ACTION,
    PAYMENT_PROOF,
    # Step 1: Basic Information
    NAME,
    PHONE,
    EMAIL,
    LOCATION,
    SOCIAL,            # Telegram / LinkedIn (optional)
    # Step 2: Profile
    PROFILE,
    # Step 3: Education
    UNIVERSITY,
    DEGREE,
    EDU_YEAR,
    GPA,
    # Step 4: Skills
    SKILLS,
    SOFT_SKILLS,
    # Step 5: Projects
    PROJECTS,
    # Step 6: Experience
    EXPERIENCE,
    # Step 7: Certificates
    CERTIFICATIONS,
    # Step 8: Languages
    LANGUAGES,
    # Photo, Document, Review, Editing
    PHOTO,
    DOCUMENT,
    REVIEW,
    EDITING
) = range(22)

# ─────────────────────────────────────────────
# /start and begin
# ─────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    context.user_data['user_id'] = user.id
    context.user_data['username'] = user.username
    context.user_data['cv_data'] = {}

    welcome_text = (
        "👋 *Welcome to Computer Concept CV Bot!*\n\n"
        "I will help you create a *professional, powerful CV* step by step.\n\n"
        "💡 *How it works:*\n"
        "• I'll ask you questions in *8 easy steps*\n"
        "• Don't worry about grammar ❌\n"
        "• Don't try to be perfect ❌\n"
        "• Just write simple ✔️\n"
        "• I will make it professional + powerful ✔️\n\n"
        "📎 *Or upload your old CV* (PDF/Word) and I'll extract the info for you!\n\n"
        "Click the button below to start 🚀"
    )

    keyboard = [[InlineKeyboardButton("🚀 Start Building CV", callback_data="start_flow")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    return SELECTING_ACTION

async def begin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start(update, context)

async def handle_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "start_flow":
        user_id = query.from_user.id
        user_db = db.get_user(user_id)
        if not user_db:
            db.update_user(user_id, status='started', payment_status='unpaid')
            payment_status = 'unpaid'
        else:
            payment_status = user_db.get('payment_status') or 'unpaid'

        if payment_status == 'pending':
            await query.message.reply_text("⏳ Your payment is currently under review by the admin. Please wait for approval.", parse_mode='Markdown')
            return ConversationHandler.END

        if payment_status != 'paid':
            msg = (
                "💰 *Payment Required*\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "To use the Computer Concept CV Builder, please pay *20 Birr*.\n\n"
                "📌 *Telebirr Account:* `0963268950`\n"
                "📌 *Name:* `Fantahun mekonen`\n\n"
                "📸 *Please upload a screenshot of your transaction receipt here.*"
            )
            await query.message.reply_text(msg, parse_mode='Markdown')
            return PAYMENT_PROOF

        msg = (
            f"{get_progress_bar(1)}\n\n"
            "💼 *Section 1: Identity & Contact*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Let's define your professional identity!\n\n"
            "👤 What is your *Full Name*?\n"
            "_(exactly how it want it on your premium CV)_\n\n"
            "📎 _Tip: Upload an existing CV to fast-track the process!_"
        )
        await query.message.reply_text(msg, reply_markup=get_nav_markup(1), parse_mode='Markdown')
        await query.message.delete()
        return NAME
    return SELECTING_ACTION

# ─────────────────────────────────────────────
# Payment Flow
# ─────────────────────────────────────────────
async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "NoUsername"
    
    db.update_user(user_id, payment_status='pending')
    
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=file_id,
            caption=f"💰 *New Payment Proof*\nUser: @{username} (ID: `{user_id}`)\nAmount: 20 Birr",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Approve", callback_data=f"approve_payment_{user_id}")],
                [InlineKeyboardButton("❌ Reject", callback_data=f"reject_payment_{user_id}")]
            ]),
            parse_mode='Markdown'
        )
    elif update.message.document:
        file_id = update.message.document.file_id
        await context.bot.send_document(
            chat_id=ADMIN_ID,
            document=file_id,
            caption=f"💰 *New Payment Proof*\nUser: @{username} (ID: `{user_id}`)\nAmount: 20 Birr",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Approve", callback_data=f"approve_payment_{user_id}")],
                [InlineKeyboardButton("❌ Reject", callback_data=f"reject_payment_{user_id}")]
            ]),
            parse_mode='Markdown'
        )
        
    await update.message.reply_text("✅ *Receipt sent to admin!* \n\nPlease wait for approval. You will receive a message once approved.", parse_mode='Markdown')
    return ConversationHandler.END

async def handle_payment_invalid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel": return await cancel(update, context)
    if text == "🔙 Back": return await start(update, context)
    
    await update.message.reply_text(
        "❌ Please upload a *photo* or *document* of your transaction receipt.",
        parse_mode='Markdown'
    )
    return PAYMENT_PROOF



# ═══════════════════════════════════════════════
# 🔥 STEP 1: BASIC INFORMATION
# ═══════════════════════════════════════════════

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel": return await cancel(update, context)
    if text == "🔙 Back": return await start(update, context)

    name = clean_input(text)
    context.user_data['cv_data']['full_name'] = name

    msg = (
        f"{get_progress_bar(1)}\n\n"
        "💼 *Section 1: Identity & Contact*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Identity secured!\n\n"
        "📞 What is your *Phone Number*?\n"
        "_(e.g., +251XXXXXXXXX or local format)_"
    )
    await update.message.reply_text(msg, reply_markup=get_nav_markup(1), parse_mode='Markdown')
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel": return await cancel(update, context)
    if text == "🔙 Back":
        msg = (
            f"{get_progress_bar(1)}\n\n"
            "🔥 *Step 1: Basic Information*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👤 What is your *Full Name*?"
        )
        await update.message.reply_text(msg, reply_markup=get_nav_markup(1), parse_mode='Markdown')
        return NAME

    phone = validate_phone(text)
    if not phone:
        await update.message.reply_text(
            "❌ Invalid format!\n"
            "Use: +251912345678 or 0912345678\n\n"
            "Please try again:",
            reply_markup=get_nav_markup(1)
        )
        return PHONE
    context.user_data['cv_data']['phone'] = phone

    msg = (
        f"{get_progress_bar(1)}\n\n"
        "🔥 *Step 1: Basic Information*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Phone saved!\n\n"
        "✉️ What is your *Email Address*?\n"
        "_(e.g., yourname@gmail.com)_"
    )
    await update.message.reply_text(msg, reply_markup=get_nav_markup(1), parse_mode='Markdown')
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel": return await cancel(update, context)
    if text == "🔙 Back":
        msg = (
            f"{get_progress_bar(1)}\n\n"
            "🔥 *Step 1: Basic Information*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📞 What is your *Phone Number*?"
        )
        await update.message.reply_text(msg, reply_markup=get_nav_markup(1), parse_mode='Markdown')
        return PHONE

    email = validate_email(text)
    if not email:
        await update.message.reply_text("❌ Invalid email format. Please try again:", reply_markup=get_nav_markup(1))
        return EMAIL
    context.user_data['cv_data']['email'] = email

    msg = (
        f"{get_progress_bar(1)}\n\n"
        "🔥 *Step 1: Basic Information*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Email saved!\n\n"
        "📍 What is your *Location*?\n"
        "_(City + Country, e.g., Addis Ababa, Ethiopia)_"
    )
    await update.message.reply_text(msg, reply_markup=get_nav_markup(1), parse_mode='Markdown')
    return LOCATION

async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel": return await cancel(update, context)
    if text == "🔙 Back":
        msg = (
            f"{get_progress_bar(1)}\n\n"
            "🔥 *Step 1: Basic Information*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✉️ What is your *Email Address*?"
        )
        await update.message.reply_text(msg, reply_markup=get_nav_markup(1), parse_mode='Markdown')
        return EMAIL

    location = clean_input(text)
    context.user_data['cv_data']['city'] = location

    msg = (
        f"{get_progress_bar(1)}\n\n"
        "🔥 *Step 1: Basic Information*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Location saved!\n\n"
        "🔗 Do you have a *Telegram username* or *LinkedIn*? _(optional)_\n\n"
        "👉 Example:\n"
        "`@myusername` or `linkedin.com/in/myprofile`\n\n"
        "Type /skip if you don't have one."
    )
    await update.message.reply_text(msg, reply_markup=get_nav_markup(1), parse_mode='Markdown')
    return SOCIAL

async def get_social(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel": return await cancel(update, context)
    if text == "🔙 Back":
        msg = (
            f"{get_progress_bar(1)}\n\n"
            "🔥 *Step 1: Basic Information*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📍 What is your *Location*?"
        )
        await update.message.reply_text(msg, reply_markup=get_nav_markup(1), parse_mode='Markdown')
        return LOCATION

    social = clean_input(text)
    context.user_data['cv_data']['social'] = social
    return await _ask_profile(update, context)

async def skip_social(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['cv_data']['social'] = ""
    return await _ask_profile(update, context)

# ═══════════════════════════════════════════════
# 🔥 STEP 2: PROFILE (Very Important Section)
# ═══════════════════════════════════════════════

async def _ask_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        f"{get_progress_bar(2)}\n\n"
        "📜 *Section 2: Professional Branding*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Define your unique professional signature!\n\n"
        "Tell me:\n"
        "• Your academic specialty\n"
        "• Core technical focus _(Fullstack, Mobile, DevOps, AI, etc.)_\n"
        "• Your career career objectives\n\n"
        "👉 *Draft simple ideas, I will refine them:* \n"
        "_\"I am a computer science student. I like build web apps.\"_\n\n"
        "✨ **Premium Result:**\n"
        "\"_Dedicated Computer Science enthusiast with technical focus on building "
        "scalable web architectures, committed to delivering high-impact solutions._\"\n\n"
        "📝 Define your brand below:"
    )
    await update.message.reply_text(msg, reply_markup=get_nav_markup(2), parse_mode='Markdown')
    return PROFILE

async def get_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel": return await cancel(update, context)
    if text == "🔙 Back":
        msg = (
            f"{get_progress_bar(1)}\n\n"
            "💼 *Section 1: Identity & Contact*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔗 Digital presence _(Telegram/LinkedIn):_"
        )
        await update.message.reply_text(msg, reply_markup=get_nav_markup(1), parse_mode='Markdown')
        return SOCIAL

    profile = clean_input(text)
    is_good, msg = check_quality(profile, min_words=8)
    if not is_good:
        await update.message.reply_text(
            f"⚠️ {msg}\n\n"
            "💡 Quality matters—aim for at least 2 clear sentences.\n"
            "Just write simple points, and the AI will handle the rest!",
            reply_markup=get_nav_markup(2)
        )
        return PROFILE
    context.user_data['cv_data']['profile'] = profile
    return await _ask_university(update, context)

# ═══════════════════════════════════════════════
# 🔥 STEP 3: EDUCATION
# ═══════════════════════════════════════════════

async def _ask_university(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        f"{get_progress_bar(3)}\n\n"
        "🎓 *Section 3: Academic Background*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🏫 What is your *Institution's name*?\n"
        "_(e.g., Addis Ababa University)_"
    )
    await update.message.reply_text(msg, reply_markup=get_nav_markup(3), parse_mode='Markdown')
    return UNIVERSITY

async def get_university(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel": return await cancel(update, context)
    if text == "🔙 Back": return await _ask_profile(update, context)

    uni = clean_input(text)
    context.user_data['cv_data']['university'] = uni

    keyboard = [
        [InlineKeyboardButton("📜 BSc / BA", callback_data="degree_bsc"),
         InlineKeyboardButton("📜 MSc / MA", callback_data="degree_msc")],
        [InlineKeyboardButton("🎓 Diploma", callback_data="degree_diploma"),
         InlineKeyboardButton("🎓 PhD", callback_data="degree_phd")],
        [InlineKeyboardButton("📝 Other", callback_data="degree_other")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    msg = (
        f"{get_progress_bar(3)}\n\n"
        "🎓 *Section 3: Academic Background*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Institution recorded!\n\n"
        "📜 Select your *Credential Level*:"
    )
    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='Markdown')
    return DEGREE

async def handle_degree_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    degree_map = {
        "degree_bsc": "BSc / BA",
        "degree_msc": "MSc / MA",
        "degree_diploma": "Diploma",
        "degree_phd": "PhD",
        "degree_other": "Other"
    }

    degree = degree_map.get(query.data, "Other")
    context.user_data['cv_data']['degree'] = degree

    msg = (
        f"🔥 *Step 3: Education*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ Degree: *{degree}*\n\n"
        f"📅 What is your *study period*?\n"
        f"_(Start year – End year, e.g., 2020 – 2024)_"
    )
    await query.edit_message_text(msg, parse_mode='Markdown')
    return EDU_YEAR

async def get_edu_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel": return await cancel(update, context)
    if text == "🔙 Back":
        # Can't easily go back from text to Inline conversion, so just re-ask university
        return await _ask_university(update, context)

    year = clean_input(text)
    context.user_data['cv_data']['edu_year'] = year

    msg = (
        f"{get_progress_bar(3)}\n\n"
        "🔥 *Step 3: Education*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Study period saved!\n\n"
        "📊 What is your *GPA*?\n"
        "_(e.g., 3.5 — only if 3.0 or above, otherwise type /skip)_"
    )
    await update.message.reply_text(msg, reply_markup=get_nav_markup(3), parse_mode='Markdown')
    return GPA

async def get_gpa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel": return await cancel(update, context)
    if text == "🔙 Back":
        msg = (
            f"{get_progress_bar(3)}\n\n"
            "🔥 *Step 3: Education*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📅 What is your *study period*?\n"
            "_(Start year – End year, e.g., 2020 – 2024)_"
        )
        await update.message.reply_text(msg, reply_markup=get_nav_markup(3), parse_mode='Markdown')
        return EDU_YEAR

    gpa_text = text.strip()
    if gpa_text.lower() == '/skip':
        return await skip_gpa(update, context)

    gpa = validate_gpa(gpa_text)
    if gpa is None:
        await update.message.reply_text(
            "❌ Invalid GPA. Enter a number between 0.0 and 4.0\n"
            "Or type /skip to skip.",
            reply_markup=get_nav_markup(3)
        )
        return GPA
    context.user_data['cv_data']['gpa'] = str(gpa)
    _build_education_string(context)
    return await _ask_skills(update, context)

async def skip_gpa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['cv_data']['gpa'] = ""
    _build_education_string(context)
    return await _ask_skills(update, context)

def _build_education_string(context):
    """Combine education sub-fields into a single education string."""
    data = context.user_data['cv_data']
    parts = []
    if data.get('university'):
        parts.append(data['university'])
    if data.get('degree'):
        parts.append(data['degree'])
    if data.get('edu_year'):
        parts.append(data['edu_year'])
    if data.get('gpa'):
        parts.append(f"GPA: {data['gpa']}")
    data['education'] = " | ".join(parts) if parts else ""

# ═══════════════════════════════════════════════
# 🔥 STEP 4: SKILLS
# ═══════════════════════════════════════════════

async def _ask_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        f"{get_progress_bar(4)}\n\n"
        "💻 *Section 4: Core Competencies*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "List your *Technical Arsenal*:\n\n"
        "• **Languages & Frameworks** _(Python, React, etc.)_\n"
        "• **Cloud & DevOps** _(AWS, Docker, Git, etc.)_\n"
        "• **Database Engineering** _(PostgreSQL, NoSQL, etc.)_\n"
        "• **Artificial Intelligence** _(PyTorch, LLMs, etc.)_\n\n"
        "👉 *Example:* \n"
        "_Python, Django, React, Docker, PostgreSQL, AWS_"
    )
    await update.message.reply_text(msg, reply_markup=get_nav_markup(4), parse_mode='Markdown')
    return SKILLS

async def get_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel": return await cancel(update, context)
    if text == "🔙 Back":
        msg = (
            f"{get_progress_bar(3)}\n\n"
            "🎓 *Section 3: Academic Background*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 Final Evaluation _(GPA):_"
        )
        await update.message.reply_text(msg, reply_markup=get_nav_markup(3), parse_mode='Markdown')
        return GPA

    skills = clean_input(text)
    context.user_data['cv_data']['skills'] = skills

    msg = (
        f"{get_progress_bar(4)}\n\n"
        "💻 *Section 4: Core Competencies*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Technical stack recorded!\n\n"
        "🧠 Now list your *Professional Soft Skills*:\n\n"
        "• Strategic Leadership & Mentorship\n"
        "• Complex Problem Solving\n"
        "• Agile Project Management\n\n"
        "👉 *Example:*\n"
        "_Leadership, Communication, Analytical Thinking_"
    )
    await update.message.reply_text(msg, reply_markup=get_nav_markup(4), parse_mode='Markdown')
    return SOFT_SKILLS

async def get_soft_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel": return await cancel(update, context)
    if text == "🔙 Back":
        msg = (
            f"{get_progress_bar(4)}\n\n"
            "🔥 *Step 4: Skills*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "💻 List your *Technical Skills*:"
        )
        await update.message.reply_text(msg, reply_markup=get_nav_markup(4), parse_mode='Markdown')
        return SKILLS

    soft_skills = clean_input(text)
    context.user_data['cv_data']['soft_skills'] = soft_skills
    return await _ask_projects(update, context)

# ═══════════════════════════════════════════════
# 🔥 STEP 5: PROJECTS (VERY IMPORTANT)
# ═══════════════════════════════════════════════

async def _ask_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        f"{get_progress_bar(5)}\n\n"
        "🚀 *Section 5: Key Projects & Portfolio*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Highlight your *Top 1–3 Engineering Projects*:\n\n"
        "For each project, detail:\n"
        "• **Project Identity**\n"
        "• **Core Impact** _(What did it solve?)_\n"
        "• **Tech Architecture**\n\n"
        "👉 *Draft simple points:* \n"
        "_\"I built an AI bot that makes CVs using Python.\"_\n\n"
        "✨ **Premium Result:**\n"
        "\"_Architected a specialized AI agent utilizing Large Language Models to "
        "automate and optimize professional CV generation, streamlining HR "
        "workflows._\"\n\n"
        "📝 Detail your projects below:"
    )
    await update.message.reply_text(msg, reply_markup=get_nav_markup(5), parse_mode='Markdown')
    return PROJECTS

async def get_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel": return await cancel(update, context)
    if text == "🔙 Back":
        msg = (
            f"{get_progress_bar(4)}\n\n"
            "💻 *Section 4: Core Competencies*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🧠 Now list your *Professional Soft Skills*:"
        )
        await update.message.reply_text(msg, reply_markup=get_nav_markup(4), parse_mode='Markdown')
        return SOFT_SKILLS

    projects = clean_input(text)
    is_good, msg = check_quality(projects, min_words=10)
    if not is_good:
        await update.message.reply_text(
            f"⚠️ {msg}\n\n"
            "💡 High-impact projects define your expertise.\n"
            "List the name, the challenge, and the tools used.",
            reply_markup=get_nav_markup(5)
        )
        return PROJECTS
    context.user_data['cv_data']['projects'] = projects
    return await _ask_experience(update, context)

# ═══════════════════════════════════════════════
# 🔥 STEP 6: EXPERIENCE
# ═══════════════════════════════════════════════

async def _ask_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        f"{get_progress_bar(6)}\n\n"
        "💼 *Section 6: Work History*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Highlight your *Professional Experience*:\n\n"
        "Detail your history:\n"
        "• **Organization & Industry**\n"
        "• **Role & Responsibilities**\n"
        "• **Key Achievements**\n"
        "• **Timeline**\n\n"
        "💡 _Entering the workforce? No problem—skip this and we'll "
        "emphasize your Core Competencies._\n\n"
        "Type /skip if you don't have experience."
    )
    await update.message.reply_text(msg, reply_markup=get_nav_markup(6), parse_mode='Markdown')
    return EXPERIENCE

async def get_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel": return await cancel(update, context)
    if text == "🔙 Back": return await _ask_projects(update, context)

    exp = clean_input(text)
    context.user_data['cv_data']['experience'] = exp
    return await _ask_certifications(update, context)

async def skip_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['cv_data']['experience'] = ""
    return await _ask_certifications(update, context)

# ═══════════════════════════════════════════════
# 🔥 STEP 7: CERTIFICATES
# ═══════════════════════════════════════════════

async def _ask_certifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        f"{get_progress_bar(7)}\n\n"
        "📜 *Section 7: Credentials & Certifications*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "List your *Verified Credentials*:\n\n"
        "• Global Certifications _(AWS, Google, Microsoft, etc.)_\n"
        "• Specialized Training Programs\n"
        "• Professional Honors\n\n"
        "👉 *Example:* \n"
        "_AWS Certified Solutions Architect – Associate_"
    )
    await update.message.reply_text(msg, reply_markup=get_nav_markup(7), parse_mode='Markdown')
    return CERTIFICATIONS

async def get_certifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel": return await cancel(update, context)
    if text == "🔙 Back": return await _ask_experience(update, context)

    certs = clean_input(text)
    context.user_data['cv_data']['certifications'] = certs
    return await _ask_languages(update, context)

async def skip_certifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['cv_data']['certifications'] = ""
    return await _ask_languages(update, context)

# ═══════════════════════════════════════════════
# 🔥 STEP 8: LANGUAGES
# ═══════════════════════════════════════════════

async def _ask_languages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        f"{get_progress_bar(8)}\n\n"
        "🌐 *Section 8: Language Proficiency*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Specify your *Linguistic Capabilities*:\n\n"
        "👉 *Format:*\n"
        "_English – Professional Working Proficiency_\n"
        "_Amharic – Native or Bilingual Proficiency_\n\n"
        "📝 Detail your languages below:"
    )
    await update.message.reply_text(msg, reply_markup=get_nav_markup(8), parse_mode='Markdown')
    return LANGUAGES

async def get_languages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel": return await cancel(update, context)
    if text == "🔙 Back": return await _ask_certifications(update, context)

    langs = clean_input(text)
    context.user_data['cv_data']['languages'] = langs

    msg = (
        "📸 *Almost there!—Professional Portrait*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Please upload a *High-Resolution Portrait* for your CV.\n\n"
        "💡 **Executive Presence Tips:**\n"
        "• Use a clean, neutral background\n"
        "• Professional business attire\n"
        "• Direct gaze with soft lighting\n\n"
        "Type /skip to proceed without a portrait."
    )
    await update.message.reply_text(msg, reply_markup=get_nav_markup(8), parse_mode='Markdown')
    return PHOTO

# ═══════════════════════════════════════════════
# Photo + Document + Review
# ═══════════════════════════════════════════════

async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['cv_data']['photo_file_id'] = None
    return await _ask_document(update, context)

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_text = update.message.text or update.message.caption or ""
    if msg_text == "❌ Cancel": return await cancel(update, context)
    if msg_text == "🔙 Back": return await _ask_languages(update, context)

    if not update.message.photo:
        await update.message.reply_text("❌ Please upload a photo or type /skip.", reply_markup=get_nav_markup(8))
        return PHOTO

    photo_file = update.message.photo[-1]
    context.user_data['cv_data']['photo_file_id'] = photo_file.file_id
    return await _ask_document(update, context)

async def _ask_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📄 *Supplementary Document (Optional)*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "You can now upload a *Reference Document* (like your existing CV in PDF or DOCX) for the admin to reference.\n\n"
        "Type /skip if you don't have any document to upload."
    )
    await update.message.reply_text(msg, reply_markup=get_nav_markup(8), parse_mode='Markdown')
    return DOCUMENT

async def get_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_text = update.message.text or update.message.caption or ""
    if msg_text == "❌ Cancel": return await cancel(update, context)
    if msg_text == "🔙 Back": 
        msg = (
            "📸 *Almost there!—Professional Portrait*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Please upload a *High-Resolution Portrait* for your CV.\n\n"
            "Type /skip to proceed without a portrait."
        )
        await update.message.reply_text(msg, reply_markup=get_nav_markup(8), parse_mode='Markdown')
        return PHOTO

    if not update.message.document:
        await update.message.reply_text("❌ Please upload a document (PDF, DOCX) or type /skip.", reply_markup=get_nav_markup(8))
        return DOCUMENT

    doc_file = update.message.document
    context.user_data['cv_data']['uploaded_document_id'] = doc_file.file_id
    return await show_review(update, context)

async def skip_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['cv_data']['uploaded_document_id'] = None
    return await show_review(update, context)

async def show_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data.get('cv_data', {})
    preview = format_cv_preview(data)

    keyboard = [
        [InlineKeyboardButton("✅ Confirm & Submit", callback_data="confirm_submit")],
        [InlineKeyboardButton("✏️ Edit Sections", callback_data="edit_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(preview, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        # Remove navigation buttons when showing review
        await update.message.reply_text("✨ *Final Phase: Review & Finalize*\n━━━━━━━━━━━━━━━━━━━━━", parse_mode='Markdown')
        await update.message.reply_text(preview, reply_markup=reply_markup, parse_mode='Markdown')
        await update.message.reply_text("💡 Please evaluate your details above.", reply_markup=ReplyKeyboardRemove())
    return REVIEW

# ═══════════════════════════════════════════════
# Cancel / Restart / Edit
# ═══════════════════════════════════════════════

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Session cancelled. Type /start to begin again.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['cv_data'] = {}
    return await start(update, context)

async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'cv_data' not in context.user_data:
        await update.message.reply_text("You haven't started building your CV yet! Type /start.")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("👤 Basic Info", callback_data="edit_personal"),
         InlineKeyboardButton("📝 Profile", callback_data="edit_profile")],
        [InlineKeyboardButton("🎓 Education", callback_data="edit_education"),
         InlineKeyboardButton("💻 Skills", callback_data="edit_skills")],
        [InlineKeyboardButton("🚀 Projects", callback_data="edit_projects"),
         InlineKeyboardButton("💼 Experience", callback_data="edit_experience")],
        [InlineKeyboardButton("📜 Certificates", callback_data="edit_certifications"),
         InlineKeyboardButton("🌐 Languages", callback_data="edit_languages")],
        [InlineKeyboardButton("📸 Photo", callback_data="edit_photo")],
        [InlineKeyboardButton("🔙 Back to Review", callback_data="back_to_review")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            "✏️ *Select a section to edit:*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "✏️ *Select a section to edit:*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    return EDITING

# ═══════════════════════════════════════════════
# Callback Query Router
# ═══════════════════════════════════════════════

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # ── Admin Approve/Reject Payment ──
    if data.startswith("approve_payment_"):
        if query.from_user.id != ADMIN_ID:
            await query.answer("❌ Unauthorized.", show_alert=True)
            return ConversationHandler.END
            
        client_id_str = data.split("_")[2]
        client_id = int(client_id_str)
        db.update_user(client_id, payment_status='paid')
        
        try:
            await context.bot.send_message(
                chat_id=client_id, 
                text="✅ *Payment Approved!*\n\nYour 20 Birr payment was successful. Click /start to begin building your CV.",
                parse_mode='Markdown'
            )
        except Exception:
            pass
            
        await query.edit_message_caption(caption=query.message.caption + "\n\n✅ *Status: APPROVED*", parse_mode='Markdown')
        await query.answer("Payment Approved!")
        return ConversationHandler.END

    if data.startswith("reject_payment_"):
        if query.from_user.id != ADMIN_ID:
            await query.answer("❌ Unauthorized.", show_alert=True)
            return ConversationHandler.END
            
        client_id_str = data.split("_")[2]
        client_id = int(client_id_str)
        db.update_user(client_id, payment_status='unpaid')
        
        try:
            await context.bot.send_message(
                chat_id=client_id, 
                text="❌ *Payment Rejected.*\n\nPlease contact the admin or type /start to try uploading your receipt again.",
                parse_mode='Markdown'
            )
        except Exception:
            pass
            
        await query.edit_message_caption(caption=query.message.caption + "\n\n❌ *Status: REJECTED*", parse_mode='Markdown')
        await query.answer("Payment Rejected!")
        return ConversationHandler.END

    # ── Confirm & Submit ──
    if data == "confirm_submit":
        try:
            user_id = context.user_data.get('user_id', 'Unknown')
            cv_data = context.user_data.get('cv_data', {})
            db.save_cv_data(user_id, cv_data)

            await query.edit_message_text(
                "✅ *Details Successfully Submitted!*\n"
                "Admin has been notified. They will review your details and send you your CV soon.",
                parse_mode='Markdown'
            )

            # ── Notify Admin with Text + Photo + Document ──
            if ADMIN_ID:
                username = context.user_data.get('username', 'N/A')
                preview = format_cv_preview(cv_data)
                admin_msg = f"🆕 New CV Submission!\nUser: @{username} (ID: `{user_id}`)\n\n{preview}"

                # 1. Send text preview to admin
                await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)

                # 2. Send user's photo to admin
                if cv_data.get('photo_file_id'):
                    try:
                        await context.bot.send_photo(
                            chat_id=ADMIN_ID,
                            photo=cv_data['photo_file_id'],
                            caption=f"📸 Photo from @{username} (ID: {user_id})"
                        )
                    except Exception as e:
                        logging.error(f"Failed to send photo to admin: {e}")

                # 3. Send uploaded document to admin
                if cv_data.get('uploaded_document_id'):
                    try:
                        await context.bot.send_document(
                            chat_id=ADMIN_ID,
                            document=cv_data['uploaded_document_id'],
                            caption=f"📄 Reference Document from @{username} (ID: {user_id})"
                        )
                    except Exception as e:
                        logging.error(f"Failed to send doc to admin: {e}")

                # 4. Send instructions
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"⚡ *Admin Instructions for @{username}* (ID: `{user_id}`)\n\n"
                         f"You can now create their CV manually.\n"
                         f"When it is ready, simply *reply to this message* with the finalized PDF file to send it back to the client! \n\n"
                         f"(Payment status will reset automatically when you reply with a document.)",
                    parse_mode='Markdown'
                )

        except Exception as e:
            print(f"DEBUG: CRITICAL ERROR IN handle_callback_query: {e}")
            logging.error(f"Failed in confirm_submit: {e}")

        return ConversationHandler.END

    # ── User Edit Actions ──
    if data == "edit_menu":
        return await edit_command(update, context)

    if data == "back_to_review":
        return await show_review(update, context)

    # ── Edit Sections ──
    section_map = {
        "edit_personal": (NAME, (
            "🔥 *Step 1: Basic Information*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👤 What is your *Full Name*?"
        )),
        "edit_profile": (PROFILE, (
            "🔥 *Step 2: Profile*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 Write your profile again:"
        )),
        "edit_education": (UNIVERSITY, (
            "🔥 *Step 3: Education*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🏫 What is your *University / College*?"
        )),
        "edit_skills": (SKILLS, (
            "🔥 *Step 4: Skills*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "💻 List your *Technical Skills*:"
        )),
        "edit_projects": (PROJECTS, (
            "🔥 *Step 5: Projects*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🚀 Describe your projects:"
        )),
        "edit_experience": (EXPERIENCE, (
            "🔥 *Step 6: Experience*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "💼 Describe your experience or /skip:"
        )),
        "edit_certifications": (CERTIFICATIONS, (
            "🔥 *Step 7: Certificates*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📜 List your certificates or /skip:"
        )),
        "edit_languages": (LANGUAGES, (
            "🔥 *Step 8: Languages*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🌐 List languages you speak + level:"
        )),
        "edit_photo": (PHOTO, (
            "📸 Please upload a new *professional photo*\n"
            "Or type /skip to remove photo."
        )),
    }

    if data in section_map:
        state, prompt = section_map[data]
        await query.edit_message_text(prompt, parse_mode='Markdown')
        return state

    return REVIEW

# ─────────────────────────────────────────────
# Admin: Forward Document to User
# ─────────────────────────────────────────────
async def admin_handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin can reply to a submission message with any document to send it to that user."""
    if update.message.from_user.id != ADMIN_ID:
        return

    # Check if this is a reply to another message
    if not update.message.reply_to_message:
        await update.message.reply_text("💡 *Tip:* To send a PDF/File to a client, reply to their submission alert with the file.", parse_mode='Markdown')
        return

    # Try to find user ID in the replied message text
    reply_text = update.message.reply_to_message.text or update.message.reply_to_message.caption or ""
    
    # Simple regex to find (ID: 1234567)
    import re
    match = re.search(r'\(ID:\s*(\d+)\)', reply_text)
    
    if not match:
        await update.message.reply_text("❌ Could not find the Client ID in that message. Please reply to the original CV notification.")
        return

    client_id = int(match.group(1))
    
    try:
        # Forward the document or photo to the user
        if update.message.document:
            await context.bot.send_document(
                chat_id=client_id,
                document=update.message.document.file_id,
                caption=update.message.caption or "📄 Your edited CV is ready!"
            )
            db.update_user(client_id, payment_status='unpaid')
        elif update.message.photo:
            await context.bot.send_photo(
                chat_id=client_id,
                photo=update.message.photo[-1].file_id,
                caption=update.message.caption or "📸 File from Admin"
            )
        else:
            await update.message.reply_text("❌ Please send a Document or Photo.")
            return

        await update.message.reply_text(f"✅ Successfully sent to Client (ID: {client_id})!")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to send: {e}")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    stats = db.get_stats()
    msg = (
        "📈 *Computer Concept CV Bot Statistics*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 *Total Registered Users:* {stats['total_users']}\n"
        f"✅ *Paid Users:* {stats['total_paid']}\n"
        f"⏳ *Pending Approvals:* {stats['total_pending']}\n\n"
        f"💰 *Total Revenue:* {stats['revenue']} Birr\n"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide a message to broadcast.\n\n"
            "*Usage:* `/broadcast Your message here`",
            parse_mode='Markdown'
        )
        return

    message = " ".join(context.args)
    user_ids = db.get_all_user_ids()
    
    success_count = 0
    fail_count = 0
    
    await update.message.reply_text(f"⏳ Broadcasting message to {len(user_ids)} users...")
    
    for uid in user_ids:
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=f"📢 *Announcement from Admin*\n\n{message}",
                parse_mode='Markdown'
            )
            success_count += 1
        except Exception:
            fail_count += 1
            
    await update.message.reply_text(
        f"✅ *Broadcast Complete*\n"
        f"Successfully sent: {success_count}\n"
        f"Failed (blocked bot/deleted): {fail_count}",
        parse_mode='Markdown'
    )

async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ Please provide a User ID and a message.\n\n"
            "*Usage:* `/send <User_ID> Your message here`",
            parse_mode='Markdown'
        )
        return

    try:
        target_uid = int(context.args[0])
        message = " ".join(context.args[1:])
        
        await context.bot.send_message(
            chat_id=target_uid,
            text=f"📢 *Message from Admin*\n\n{message}",
            parse_mode='Markdown'
        )
        
        await update.message.reply_text(f"✅ Successfully sent message to ID: {target_uid}")
    except ValueError:
        await update.message.reply_text("❌ Invalid User ID format. Must be numbers.")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to send: {e}")
