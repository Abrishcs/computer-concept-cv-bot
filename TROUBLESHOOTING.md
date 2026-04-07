# Troubleshooting "Bad Gateway" Error on Render

## The Error You're Seeing:
```
Bad Gateway
Request ID: 9e854145aac08cf6-SEA
This service is currently unavailable.
```

This means your bot is crashing when it starts. Let's fix it!

---

## Step 1: Check Render Logs (MOST IMPORTANT)

1. Go to **Render Dashboard**
2. Click on your **web service** (cv-builder-bot)
3. Click **"Logs"** tab on the left
4. Look for **RED error messages**

### Common Errors You Might See:

#### Error 1: "ModuleNotFoundError: No module named 'requests'"
**Solution:** I just fixed this! Push the updated requirements.txt

#### Error 2: "telegram.error.InvalidToken"
**Solution:** BOT_TOKEN is wrong or not set
- Check Environment Variables in Render
- Make sure BOT_TOKEN is exactly: `8648200196:AAFTpktAdDQYwbVhm9QUOio8YJCcS4xP8uU`

#### Error 3: "ADMIN_ID is not set" or "Invalid ADMIN_ID"
**Solution:** ADMIN_ID is wrong or not set
- Check Environment Variables in Render
- Make sure ADMIN_ID is exactly: `8514110765` (no quotes, just numbers)

#### Error 4: "Address already in use" or "Port 10000 is already in use"
**Solution:** Multiple instances running
- This shouldn't happen on Render, but if it does, redeploy

#### Error 5: "sqlite3.OperationalError: unable to open database file"
**Solution:** Permission issue with database
- This is normal on first deploy, should auto-fix

---

## Step 2: Push the Fix I Just Made

I added `requests` to requirements.txt. Let's push it:

```bash
git add requirements.txt
git commit -m "Add requests library to requirements"
git push origin main
```

Render will automatically redeploy!

---

## Step 3: Verify Environment Variables

Go to Render Dashboard → Your Service → Environment

Make sure you have:

| Key | Value | Status |
|-----|-------|--------|
| `BOT_TOKEN` | `8648200196:AAFTpktAdDQYwbVhm9QUOio8YJCcS4xP8uU` | ✅ |
| `ADMIN_ID` | `8514110765` | ✅ |
| `PORT` | `10000` | ✅ (auto-set) |

**Important:** 
- No quotes around values
- No extra spaces
- ADMIN_ID must be numbers only

---

## Step 4: Manual Redeploy

If auto-deploy doesn't work:

1. Go to Render Dashboard
2. Click your service
3. Click **"Manual Deploy"** button
4. Select **"Clear build cache & deploy"**
5. Wait 2-3 minutes

---

## Step 5: Test After Deploy

Once logs show "🚀 Computer Concept CV Builder Bot is starting...":

1. **Test Health Check:**
   - Visit: `https://your-service-name.onrender.com`
   - Should see: "Bot is alive!"

2. **Test Bot:**
   - Open Telegram
   - Send `/start` to your bot
   - Should get welcome message

---

## Common Solutions

### Solution 1: Wrong Bot Token
```bash
# Get your bot token again from @BotFather
# Update in Render Environment Variables
# Redeploy
```

### Solution 2: Bot Running Elsewhere
- Make sure bot is NOT running on your local computer
- Only ONE instance of a Telegram bot can run at a time
- Stop local bot if running

### Solution 3: Render Service Issues
- Sometimes Render has temporary issues
- Wait 5 minutes and try again
- Check Render status: https://status.render.com/

---

## What the Logs Should Show (When Working):

```
Starting dummy web server on port 10000 (for Render health check)
DEBUG: ADMIN_ID loaded as 8514110765
🚀 Computer Concept CV Builder Bot is starting...
```

---

## If Still Not Working

**Share the Render logs with me!**

Copy the error messages from Render logs and I'll help you fix it.

To get logs:
1. Render Dashboard → Your Service → Logs
2. Copy the RED error messages
3. Share them with me

---

## Quick Fix Checklist

- [ ] Push updated requirements.txt (I just fixed it)
- [ ] Verify BOT_TOKEN in Render environment variables
- [ ] Verify ADMIN_ID in Render environment variables
- [ ] Stop any local bot instances
- [ ] Manual redeploy on Render
- [ ] Check logs for errors
- [ ] Test health check URL
- [ ] Test bot with /start

---

**Next Step:** Push the requirements.txt fix I just made!
