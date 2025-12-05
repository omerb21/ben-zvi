# Render Monitoring & Alerts Setup

## Overview
This document describes how to set up monitoring and alerts in Render for the ben-zvi backend.

## Setting Up Alerts in Render Dashboard

### 1. Navigate to Your Service
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Select your backend service

### 2. Configure Deploy Notifications
1. Go to **Settings** → **Notifications**
2. Enable notifications for:
   - **Deploy started**
   - **Deploy succeeded**
   - **Deploy failed** (CRITICAL)
3. Choose notification channels:
   - Email (recommended)
   - Slack webhook (if available)

### 3. Set Up Health Checks
1. Go to **Settings** → **Health & Alerts**
2. Configure health check endpoint:
   - Path: `/api/v1/admin/stats` (lightweight endpoint)
   - Interval: 30 seconds
3. Enable alerts for:
   - Service down
   - High response time (>5s)

### 4. Monitor Logs for 500 Errors
1. Go to **Logs** tab
2. Use filter: `status=500` or `ERROR`
3. Consider setting up log drain to external service for advanced alerting

## Recommended External Monitoring (Optional)

### UptimeRobot (Free)
1. Create account at [uptimerobot.com](https://uptimerobot.com)
2. Add HTTP monitor for your Render URL
3. Set check interval: 5 minutes
4. Configure email/SMS alerts

### Sentry (Error Tracking)
1. Install: `pip install sentry-sdk[fastapi]`
2. Add to `main.py`:
```python
import sentry_sdk
sentry_sdk.init(dsn="YOUR_SENTRY_DSN")
```

## Application-Level Logging
The backend now includes timing logs for PDF operations:
- `[PDF-TIMING] Advice PDF generated in X.XXs`
- `[PDF-TIMING] Packet generated in X.XXs`
- `[PDF-TIMING] Signing completed in X.XXs`

These logs appear in Render's log viewer and can help identify performance issues.

## Neon Database Monitoring
1. Go to [Neon Console](https://console.neon.tech)
2. Select your project
3. View **Monitoring** tab for:
   - Connection count
   - Query performance
   - Storage usage
