# Railway Deployment Guide

This guide covers deploying the Conviction Bot to Railway for 24/7 operation.

## Prerequisites

1. **Kalshi Account**: Set up API access and download your private key
2. **Railway Account**: Sign up at [railway.app](https://railway.app)
3. **GitHub Repository**: Push your code to GitHub

## Step 1: Prepare Environment Variables

You'll need these environment variables in Railway:

- `KALSHI_API_KEY_ID`: Your API key ID from Kalshi
- `KALSHI_PRIVATE_KEY_PATH`: Path to private key file (set to `/app/kalshi_private_key.pem`)
- `KALSHI_DEMO`: Set to `false` for live trading, `true` for demo

## Step 2: Upload Private Key

Railway doesn't support file uploads directly. You have two options:

### Option A: Base64 Environment Variable (Recommended)
1. Encode your private key file:
   ```bash
   base64 -i kalshi_private_key.pem
   ```
2. Add the output as environment variable `KALSHI_PRIVATE_KEY_BASE64`
3. Update `kalshi_auth.py` to decode from base64 if file doesn't exist

### Option B: Create Volume Mount
1. Create a Railway volume
2. Upload your private key file to the volume
3. Mount to `/app/kalshi_private_key.pem`

## Step 3: Deploy to Railway

1. **Connect Repository**:
   - Go to Railway dashboard
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your kalshi-bot repository

2. **Configure Environment**:
   - Go to Variables tab
   - Add all required environment variables
   - Set `KALSHI_DEMO=false` for live trading

3. **Deploy**:
   - Railway will automatically detect the Python app
   - Uses `requirements.txt` for dependencies
   - Starts with command from `Procfile`: `python conviction_bot_live.py`

## Step 4: Monitor Deployment

1. **Check Logs**:
   - Go to Deployments tab
   - View build and runtime logs
   - Look for "🚀 Starting Conviction Bot LIVE" message

2. **Verify Operation**:
   - Bot should display account balance
   - Monitor for trading signals
   - Check for any authentication errors

## Step 5: Production Checklist

- [ ] Environment variables set correctly
- [ ] Private key accessible (test authentication)
- [ ] `KALSHI_DEMO=false` for live trading
- [ ] Sufficient account balance
- [ ] Bot starts successfully and shows balance
- [ ] Logs show polling activity during trading windows

## Troubleshooting

### Authentication Errors
- Verify `KALSHI_API_KEY_ID` is correct
- Check private key file path and permissions
- Test authentication in demo mode first

### Bot Not Starting
- Check Python version compatibility (3.8+)
- Verify all dependencies in `requirements.txt`
- Review build logs for missing packages

### Trading Issues
- Ensure sufficient account balance
- Check if markets are available and active
- Verify time zone settings (bot uses UTC)

## Security Notes

- Never commit private keys to git
- Use Railway's encrypted environment variables
- Regularly rotate API keys
- Monitor account for unauthorized activity

## Scaling

Railway automatically handles:
- Server restarts on crashes
- Memory and CPU scaling
- Network connectivity
- Log aggregation

## Cost

Railway pricing:
- $5/month for hobby plan
- Includes 500 hours runtime (sufficient for 24/7)
- Additional usage billed separately