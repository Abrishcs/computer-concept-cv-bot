# Deployment Guide for Render

## Pre-Deployment Checklist

### ✅ Fixed Issues:
1. Created `Procfile` - Tells Render how to start your app
2. Created `runtime.txt` - Specifies Python 3.11
3. Created `render.yaml` - Render configuration file
4. Fixed `requirements.txt` - Added version pins for stability
5. Updated `.gitignore` - Ensures database files aren't pushed

## Deployment Steps

### 1. Push to GitHub

```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### 2. Deploy on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Render will auto-detect the `render.yaml` configuration

### 3. Configure Environment Variables

In Render dashboard, add these environment variables:

- `BOT_TOKEN` = Your Telegram Bot Token (from @BotFather)
- `ADMIN_ID` = Your Telegram User ID (numeric)
- `PORT` = 10000 (already set in render.yaml)

### 4. Important Notes

#### Database Persistence
- Your SQLite database (`cv_builder.db`) will be created on Render
- ⚠️ **WARNING**: Render's free tier has ephemeral storage
- Database will reset when the service restarts
- For production, consider upgrading to a paid plan or using PostgreSQL

#### Health Check
- The bot includes a dummy HTTP server on port 10000
- This keeps Render's health check happy
- The server responds with "Bot is alive!" at the root URL

#### Free Tier Limitations
- Service sleeps after 15 minutes of inactivity
- First request after sleep takes ~30 seconds to wake up
- 750 hours/month free (enough for 1 service running 24/7)

## Troubleshooting

### Bot Not Responding
1. Check Render logs for errors
2. Verify `BOT_TOKEN` is correct
3. Ensure bot is not running elsewhere (only one instance allowed)

### Payment Notifications Not Working
1. Verify `ADMIN_ID` is set correctly
2. Get your Telegram ID by messaging @userinfobot
3. Must be numeric (e.g., 123456789, not @username)

### Database Issues
- If data disappears, it's because Render restarted
- Consider using Render's PostgreSQL addon for persistence
- Or upgrade to a paid plan with persistent disk

## Testing Deployment

After deployment:

1. Send `/start` to your bot on Telegram
2. Check Render logs for any errors
3. Test the payment flow
4. Verify admin notifications work

## Monitoring

- View logs: Render Dashboard → Your Service → Logs
- Check health: Visit your Render URL (e.g., https://your-app.onrender.com)
- Should see "Bot is alive!"

## Support

If deployment fails, check:
- Python version compatibility (using 3.11)
- All dependencies install correctly
- Environment variables are set
- GitHub repository is connected properly
