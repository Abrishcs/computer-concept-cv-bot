# Pre-Deployment Checklist

## Before Pushing to GitHub

- [ ] Review all changes
- [ ] Ensure `.env` file is NOT in git (check `.gitignore`)
- [ ] Verify `cv_builder.db` is NOT in git
- [ ] Commit all new files

```bash
git status
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

## On Render Dashboard

- [ ] Create new Web Service
- [ ] Connect GitHub repository
- [ ] Verify `render.yaml` is detected
- [ ] Add environment variable: `BOT_TOKEN`
- [ ] Add environment variable: `ADMIN_ID`
- [ ] Click "Create Web Service"

## After Deployment

- [ ] Check deployment logs for errors
- [ ] Visit service URL (should see "Bot is alive!")
- [ ] Test bot with `/start` command
- [ ] Test payment flow
- [ ] Verify admin receives notifications
- [ ] Test `/test_admin` command

## Get Your Telegram User ID

If you don't know your ADMIN_ID:
1. Message @userinfobot on Telegram
2. It will reply with your numeric ID
3. Use that number (not your @username)

## Troubleshooting

### Bot doesn't respond
- Check Render logs
- Verify BOT_TOKEN is correct
- Ensure bot isn't running elsewhere

### Admin notifications don't work
- Verify ADMIN_ID is numeric
- Start a conversation with your bot first
- Check Render logs for errors

### Database resets
- This is normal on free tier
- Upgrade to paid plan for persistence
- Or use PostgreSQL addon

## Success Indicators

✅ Render shows "Live" status
✅ Service URL returns "Bot is alive!"
✅ Bot responds to `/start`
✅ Payment flow works
✅ Admin receives notifications
✅ No errors in logs

---

**Ready to deploy!** 🚀
