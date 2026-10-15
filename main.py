import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from google import genai
from google.genai import types

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

# Render পোর্ট সক্রিয় রাখার সার্ভার
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Live and Active!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

def analyze_and_generate_takedown(image_bytes: bytes, user_command: str) -> dict:
    system_prompt = """
    You are an Autonomous Cyber Defense & Platform Compliance Engine.
    Process incoming evidence to generate a FORMAL LEGAL TAKEDOWN DOSSIER for Meta Platforms.

    STRICT RULES:
    - Inject high-priority liability phrasing: "Statutory Preservation Demand", "Civil Harm Escalation", "Immunity Forfeiture".
    - Output must be purely authoritative legal language.

    Return STRICT JSON:
    {
        "target_category": "HARASSMENT / INCITEMENT / DEFAMATION",
        "email_subject": "Formal escalation subject line...",
        "legal_notice_body": "Formal legal letter citing exact Meta clauses...",
        "escalation_desk": "legal@fb.com"
    }
    """
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            f"EVIDENCE DETAILS: {user_command}"
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
        "🛡️ Ariyan Humo Guard AI প্রস্তুত!\n\n"
        "টার্গেট পোস্ট, পেজ বা ফেক আইডির স্ক্রিনশট পাঠান এবং ক্যাপশনে লিংক সহ ১-২ লাইনে সমস্যাটি জানিয়ে দিন।"
    )

async def handle_evidence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    caption = update.message.caption or "Emergency Legal Takedown Demand"
    
    status_msg = await update.message.reply_text("⏳ প্রমাণ রিসিভ হয়েছে। এআই মেটার পলিসি কোড ও এসকেলেশন ট্রিপওয়্যার তৈরি করছে...")
    
    file = await context.bot.get_file(photo.file_id)
    temp_img = "evidence_temp.png"
    await file.download_to_drive(temp_img)
    
    with open(temp_img, "rb") as f:
        img_data = f.read()
        
    try:
        result = analyze_and_generate_takedown(img_data, user_command=caption)
        pdf_filename = "Meta_Legal_Action_Dossier.pdf"
        create_forensic_pdf(pdf_filename, result["legal_notice_body"], temp_img)
        
        await status_msg.edit_text(
            f"✅ কেস বিশ্লেষণ সম্পন্ন!\n\n"
            f"🎯 টার্গেটেড ডেস্ক: {result.get('escalation_desk', 'legal@fb.com')}\n"
            f"📌 বিষয়: {result.get('email_subject', 'Takedown Notice')}\n\n"
            "মেটার লিগ্যাল ডেস্কে পাঠানোর জন্য অফিসিয়াল ফাইলটি তৈরি হয়েছে:"
        )
        
        with open(pdf_filename, "rb") as doc:
            await update.message.reply_document(
                document=doc,
                filename="Official_Meta_Legal_Dossier.pdf",
                caption="📁 অফিসিয়াল লিগ্যাল নোটিশ ও এভিডেন্স ফাইল প্রস্তুত।"
            )
    except Exception as e:
        await status_msg.edit_text(f"⚠️ প্রক্রিয়াকরণে সমস্যা হয়েছে: {str(e)}")

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_evidence))
    print("বট সফলভাবে সক্রিয় রয়েছে...")
    app.run_polling()
