import logging
import os
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters
)
import handlers

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Error: BOT_TOKEN not found in .env file.")
        return

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Conversation Handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', handlers.start),
            MessageHandler(filters.Regex('^(start|Start)$'), handlers.begin)
        ],
        states={
            # ── Start ──
            handlers.SELECTING_ACTION: [
                CallbackQueryHandler(handlers.handle_start_callback, pattern="^start_flow$")
            ],

            # ── Payment ──
            handlers.PAYMENT_PROOF: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, handlers.handle_payment_proof),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_payment_invalid)
            ],

            # ── 🔥 Step 1: Basic Information ──
            handlers.NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_name)
            ],
            handlers.PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_phone)
            ],
            handlers.EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_email)
            ],
            handlers.LOCATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_location)
            ],
            handlers.SOCIAL: [
                CommandHandler('skip', handlers.skip_social),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_social)
            ],

            # ── 🔥 Step 2: Profile ──
            handlers.PROFILE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_profile)
            ],

            # ── 🔥 Step 3: Education ──
            handlers.UNIVERSITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_university)
            ],
            handlers.DEGREE: [
                CallbackQueryHandler(handlers.handle_degree_selection, pattern="^degree_")
            ],
            handlers.EDU_YEAR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_edu_year)
            ],
            handlers.GPA: [
                CommandHandler('skip', handlers.skip_gpa),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_gpa)
            ],

            # ── 🔥 Step 4: Skills ──
            handlers.SKILLS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_skills)
            ],
            handlers.SOFT_SKILLS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_soft_skills)
            ],

            # ── 🔥 Step 5: Projects ──
            handlers.PROJECTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_projects)
            ],

            # ── 🔥 Step 6: Experience ──
            handlers.EXPERIENCE: [
                CommandHandler('skip', handlers.skip_experience),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_experience)
            ],

            # ── 🔥 Step 7: Certificates ──
            handlers.CERTIFICATIONS: [
                CommandHandler('skip', handlers.skip_certifications),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_certifications)
            ],

            # ── 🔥 Step 8: Languages ──
            handlers.LANGUAGES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_languages)
            ],

            # ── Photo + Document + Review + Edit ──
            handlers.PHOTO: [
                MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), handlers.get_photo),
                CommandHandler('skip', handlers.skip_photo)
            ],
            handlers.DOCUMENT: [
                MessageHandler(filters.Document.ALL | (filters.TEXT & ~filters.COMMAND), handlers.get_document),
                CommandHandler('skip', handlers.skip_document)
            ],
            handlers.REVIEW: [
                CallbackQueryHandler(handlers.handle_callback_query)
            ],
            handlers.EDITING: [
                CallbackQueryHandler(handlers.handle_callback_query)
            ],
        },
        fallbacks=[
            CommandHandler('cancel', handlers.cancel),
            CommandHandler('restart', handlers.restart),
            CommandHandler('edit', handlers.edit_command),
        ],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(handlers.handle_callback_query))

    # Global commands (outside conversation to allow access anytime)
    application.add_handler(CommandHandler('cancel', handlers.cancel))
    application.add_handler(CommandHandler('restart', handlers.restart))
    application.add_handler(CommandHandler('edit', handlers.edit_command))
    application.add_handler(CommandHandler('test_admin', handlers.test_admin))
    application.add_handler(CommandHandler('stats', handlers.stats_command))
    application.add_handler(CommandHandler('broadcast', handlers.broadcast_command))
    application.add_handler(CommandHandler('send', handlers.send_command))

    # Admin: Forward documents/photos to users by replying to alerts
    application.add_handler(MessageHandler(
        (filters.Document.ALL | filters.PHOTO) & ~filters.COMMAND,
        handlers.admin_handle_document
    ))

    print("🚀 Computer Concept CV Builder Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
