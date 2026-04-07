# Keep Your Render Bot Awake 24/7

## Problem
Render's free tier puts your service to sleep after 15 minutes of inactivity.

## Solutions

### Option 1: Render Cron Job (Recommended) ✅

I've already configured this for you!

**What I Added:**
- `ping_service.py` - Script that pings your service
- Updated `render.yaml` - Added cron job configuration

**How to Enable:**

1. Push the changes to GitHub:
```bash
git add .
git commit -m "Add cron job to keep service awake"
git push origin main
```

2. On Render Dashboard:
   - Your cron job will be auto-created from `render.yaml`
   - Go to the cron job settings
   - Add environment variable:
     - **Key:** `SERVICE_URL`
     - **Value:** Your Render service URL (e.g., `https://cv-builder-bot.onrender.com`)

3. The cron job will ping your service every 14 minutes automatically!

**Cost:** FREE (Render provides free cron jobs)

---

### Option 2: Cron-Job.org (External Service)

**Steps:**

1. Go to https://cron-job.org/en/
2. Sign up for free account
3. Create new cron job:
   - **Title:** Keep CV Bot Awake
   - **URL:** Your Render service URL (e.g., `https://cv-builder-bot.onrender.com`)
   - **Schedule:** Every 14 minutes
   - **Method:** GET

**Pros:** 
- Easy to set up
- No code changes needed
- Web dashboard

**Cons:**
- Requires external account
- Less control

---

### Option 3: UptimeRobot (Monitoring + Keep Awake)

**Steps:**

1. Go to https://uptimerobot.com/
2. Sign up for free account (50 monitors free)
3. Add new monitor:
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** CV Bot
   - **URL:** Your Render service URL
   - **Monitoring Interval:** 5 minutes (free tier)

**Pros:**
- Also monitors uptime
- Email alerts if service goes down
- Free tier is generous

**Cons:**
- 5-minute interval (service might sleep briefly)

---

### Option 4: GitHub Actions (Free)

Create `.github/workflows/keep-alive.yml`:

```yaml
name: Keep Render Service Awake

on:
  schedule:
    - cron: '*/14 * * * *'  # Every 14 minutes
  workflow_dispatch:  # Manual trigger

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Service
        run: |
          curl -f https://your-app-name.onrender.com || exit 1
```

**Pros:**
- Free with GitHub
- No external service needed
- Version controlled

**Cons:**
- Requires GitHub Actions knowledge
- Might have slight delays

---

## Recommended Setup

**Best Option:** Use Render's built-in cron job (Option 1)
- Already configured for you
- Free and reliable
- No external dependencies

**Backup Option:** Add UptimeRobot (Option 3)
- Provides monitoring
- Email alerts
- Extra reliability

---

## How to Get Your Service URL

1. Go to Render Dashboard
2. Click on your web service
3. Copy the URL at the top (e.g., `https://cv-builder-bot.onrender.com`)
4. Use this URL in:
   - Render cron job `SERVICE_URL` variable
   - External cron services
   - GitHub Actions workflow

---

## Testing

After setting up:

1. **Check if it works:**
   - Wait 14 minutes
   - Check Render logs for ping activity
   - Should see: "✅ Service is alive!"

2. **Monitor for 1 hour:**
   - Service should never sleep
   - Bot should respond instantly

3. **Test bot response:**
   - Send `/start` to your bot
   - Should respond immediately (no cold start delay)

---

## Troubleshooting

### Cron job not running
- Check Render cron job logs
- Verify `SERVICE_URL` is set correctly
- Ensure cron job is deployed

### Service still sleeping
- Increase ping frequency (every 10 minutes)
- Check if cron job is actually running
- Verify service URL is correct

### Too many requests error
- Reduce ping frequency to every 14 minutes
- Render free tier has rate limits

---

## Cost Comparison

| Method | Cost | Reliability | Setup Difficulty |
|--------|------|-------------|------------------|
| Render Cron | FREE | ⭐⭐⭐⭐⭐ | Easy |
| Cron-Job.org | FREE | ⭐⭐⭐⭐ | Very Easy |
| UptimeRobot | FREE | ⭐⭐⭐⭐⭐ | Easy |
| GitHub Actions | FREE | ⭐⭐⭐⭐ | Medium |

---

## Next Steps

1. Push the changes I made to GitHub
2. Set up the Render cron job
3. Add `SERVICE_URL` environment variable
4. Test for 1 hour
5. Enjoy your 24/7 bot! 🚀

---

**Status:** ✅ Configured and Ready
**Recommended:** Render Cron Job (Option 1)
