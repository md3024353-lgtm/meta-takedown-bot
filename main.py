import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from google import genai
from google.genai import types

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

def analyze_and_generate_takedown(image_bytes: bytes, user_command: str) -> dict:
    system_prompt = """
    You are an Autonomous Cyber Defense & Platform Compliance Engine.
    Your mission: Process incoming evidence to generate a FORMAL LEGAL TAKEDOWN or TERMINATION DOSSIER for Meta Platforms (Facebook/Instagram).

    The incident falls under one of these core categories:
    1. FAKE ACCOUNT / CLONED PROFILE: Cite Meta Section 12 (Inauthentic Representation, Identity Fraud, Impersonation). Demand immediate permanent account termination.
    2. DEFAMATORY / HARASSMENT PAGE: Cite Coordinated Inauthentic Behavior (CIB), Meta Section 3.2, systematic public character assassination, and platform liability. Demand total page deplatforming.
    3. ABUSIVE POST / VIDEO / DEEPFAKE: Cite Section 12 (Bullying & Harassment), Non-Consensual Altered/Synthetic Media, Section 512 DMCA, and Intermediary Liability. Demand expeditious takedown.
    4. PRIVACY VIOLATIONS / DOXXING: Demand emergency data removal under global statutory privacy laws and Meta Privacy Policy.

    STRICT RULES:
    - Inject high-priority liability phrasing: "Statutory Preservation Demand", "Civil Harm Escalation", "Immunity Forfeiture".
    - Output must be purely authoritative legal language.

    Return STRICT JSON:
    {
        "target_category": "HARASSMENT_POST / DEFAMATORY_PAGE / FAKE_ACCOUNT / DOXXING",
        "email_subject": "Formal high-priority subject line with escalation tag...",
        "legal_notice_body": "Authoritative formal demand letter citing exact Meta clauses, requesting immediate action...",
        "escalation_desk": "ip@fb.com / legal@fb.com / Meta Impersonation Escalations"
    }
    """

    user_prompt = f"""
    INCIDENT DETAILS & COMMAND: "{user_command}"
    Analyze the visual evidence and incident details, classify the target, and generate the complete legal dossier.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            user_prompt
        ],
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json"
        )
    )
    return json.loads(response.text)

def create_forensic_pdf(filename: str, legal_text: str, image_path: str):
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, 750, "CYBER FORENSIC & LEGAL ESCALATION DOSSIER")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, 735, "OFFICIAL NOTICE UNDER META COMMUNITY STANDARDS")
    
    c.setFont("Helvetica", 9)
    y = 705
    for line in legal_text.split("\n")[:28]:
        c.drawString(40, y, line[:95])
        y -= 14
        
    c.showPage()
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, 750, "ANNEXURE A: VERIFIED FORENSIC TARGET EVIDENCE")
    c.drawImage(image_path, 40, 240, width=520, height=480, preserveAspectRatio=True)
    c.save()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ Ariyan Humo Guard AI - সাইবার ডিফেন্স বট প্রস্তুত!\n\n"
        "আমি মেটার সকল অপপ্রচার, ফেক আইডি এবং হ্যারাসমেন্টের বিরুদ্ধে দ্রুত লিগ্যাল অ্যাকশন ডসিয়ার তৈরি করতে পারি।\n\n"
        "📌 ব্যবহারের নিয়ম:\n"
        "টার্গেট পোস্ট, পেজ বা ফেক আইডির স্ক্রিনশট পাঠান এবং ক্যাপশনে লিংক সহ ১-২ লাইনে সমস্যাটি জানিয়ে দিন।"
    )

async def handle_evidence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    caption = update.message.caption or "Emergency Legal Takedown & Termination"
    
    status_msg = await update.message.reply_text("⏳ প্রমাণ রিসিভ হয়েছে। এআই মেটার স্পেসিফিক পলিসি কোড ও এসকেলেশন ট্রিপওয়্যার তৈরি করছে...")
    
    file = await context.bot.get_file(photo.file_id)
    temp_img = "evidence_temp.png"
    await file.download_to_drive(temp_img)
    
    with open(temp_img, "rb") as f:
        img_data = f.read()
        
    result = analyze_and_generate_takedown(img_data, user_command=caption)
    
    pdf_filename = "Meta_Legal_Action_Dossier.pdf"
    create_forensic_pdf(pdf_filename, result["legal_notice_body"], temp_img)
    
    await status_msg.edit_text(
        f"✅ কেস ক্যাটাগরি: {result['target_category']}\n"
        f"🎯 টার্গেটেড ডেস্ক: {result['escalation_desk']}\n"
        f"📌 বিষয়: {result['email_subject']}\n\n"
        "মেটার লিগ্যাল ডেস্কে পাঠানোর জন্য কমপ্লিট আইনি ফাইল তৈরি হয়েছে:"
    )
    
    with open(pdf_filename, "rb") as doc:
        await update.message.reply_document(
            document=doc,
            filename="Official_Meta_Legal_Dossier.pdf",
            caption="📁 অফিসিয়াল লিগ্যাল নোটিশ ও এভিডেন্স ফাইল প্রস্তুত।"
        )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_evidence))
    print("বট সক্রিয় রয়েছে...")
    app.run_polling()
