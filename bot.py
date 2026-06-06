from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import secrets
import string
import time
import random

WAITING_FOR_OTP = 1

# Random Password Generator
def generate_password(length=12):
    characters = string.ascii_letters + string.digits + "!@#$"
    return ''.join(secrets.choice(characters) for i in range(length))

# Random 18+ Date of Birth Generator
def generate_dob():
    year = random.randint(1990, 2005) # 18+ years secure ga undadaniki
    month = random.randint(1, 12)
    day = random.randint(1, 28) # 31st/Leap year issues rakunda 1-28 pettam
    
    # Format: DD/MM/YYYY (Ex: 15/08/1998)
    return f"{day:02d}/{month:02d}/{year}"

async def create_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 3:
        await update.message.reply_text("Format wrong boss! Ila ivvandi: \n/create <Name> <Username> <Email>")
        return ConversationHandler.END
    
    name, username, email = args
    password = generate_password()
    dob = generate_dob() # Kotha DOB ikkada generate avtundi
    
    context.user_data['username'] = username
    context.user_data['password'] = password
    context.user_data['dob'] = dob

    await update.message.reply_text(f"Process start chestunnanu...\nName: {name}\nUsername: {username}\nEmail: {email}\nDOB: {dob}")

    # Render server kosam Headless settings
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox") 
    chrome_options.add_argument("--disable-dev-shm-usage") 

    driver = webdriver.Chrome(options=chrome_options)
    context.user_data['driver'] = driver
    
    try:
        # Mee shopping website URL ikkada pettandi
        driver.get("https://www.instagram.com/accounts/emailsignup/?next=")
        wait = WebDriverWait(driver, 10)
        
        # Details entry
        wait.until(EC.presence_of_element_located((By.NAME, "fullName"))).send_keys(name)
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "email").send_keys(email)
        driver.find_element(By.NAME, "password").send_keys(password)
        
        # 🟢 DOB entry: Mee website lo DOB box name batti "dateOfBirth" ni marchandi
        driver.find_element(By.NAME, "dateOfBirth").send_keys(dob)
        
        # Submit button click
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        await update.message.reply_text(f"✅ Details submit ayyayi. \n{email} ki vachina OTP ni ikkada enter cheyyandi.")
        return WAITING_FOR_OTP
        
    except Exception as e:
        await update.message.reply_text(f"❌ Step 1 Fail ayyindi! Error: {e}")
        driver.quit()
        context.user_data.clear()
        return ConversationHandler.END

async def receive_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp_code = update.message.text
    driver = context.user_data.get('driver')
    username = context.user_data.get('username')
    password = context.user_data.get('password')
    dob = context.user_data.get('dob')
    
    await update.message.reply_text("OTP verify chestunnanu...")
    
    try:
        wait = WebDriverWait(driver, 10)
        otp_box = wait.until(EC.presence_of_element_located((By.NAME, "otpField")))
        otp_box.send_keys(otp_code)
        
        driver.find_element(By.CSS_SELECTOR, "button[class='verify-btn']").click()
        time.sleep(5) 
        
        success_text = (
            "🎉 **ACCOUNT CREATION SUCCESSFUL!** 🎉\n\n"
            f"👤 **Username:** `{username}`\n"
            f"🔑 **Password:** `{password}`\n"
            f"🎂 **DOB Used:** `{dob}`"
        )
        await update.message.reply_text(success_text, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ **ACCOUNT CREATION FAILED!** \nDetails: {e}")
        
    finally:
        driver.quit()
        context.user_data.clear()
        
    return ConversationHandler.END

def main():
    # MEE BOT TOKEN IKKADA PETTANDI
    BOT_TOKEN = "8728596690:AAFqizDl2Mw87Jodmsz2hw5w5pkEesv7X4s"
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('create', create_account)],
        states={
            WAITING_FOR_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_otp)]
        },
        fallbacks=[]
    )

    application.add_handler(conv_handler)
    print("Bot start ayyindi...")
    application.run_polling()

if __name__ == '__main__':
    main()
