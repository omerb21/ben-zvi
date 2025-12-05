# Neon Branches - Quick Backup Before Major Changes

## Overview
Neon's branching feature allows you to create instant database snapshots before making risky changes.

## When to Create a Branch
- Before running Alembic migrations on production
- Before bulk data imports
- Before running `sync_remote` for disaster recovery
- Before any destructive operations

## How to Create a Branch

### Via Neon Console (Recommended)
1. Go to [Neon Console](https://console.neon.tech)
2. Select your project
3. Go to **Branches** tab
4. Click **Create Branch**
5. Name it descriptively: `backup-before-migration-2024-01-15`
6. Select parent branch (usually `main`)
7. Click **Create**

### Via Neon CLI
```bash
# Install Neon CLI
npm install -g neonctl

# Authenticate
neonctl auth

# Create branch
neonctl branches create --project-id YOUR_PROJECT_ID --name backup-before-migration
```

## How to Restore from a Branch

### Option 1: Switch Connection String
1. Get the branch's connection string from Neon Console
2. Update `DATABASE_URL` in Render environment variables
3. Redeploy

### Option 2: Promote Branch to Main
1. In Neon Console, go to the branch
2. Click **Promote to Primary**
3. This makes the branch the new main database

## Best Practices
- Delete old branches after successful migrations (Neon has branch limits on free tier)
- Name branches with dates for easy identification
- Test migrations on a branch first before applying to main

## Alembic Migration Workflow with Branches

```bash
# 1. Create backup branch in Neon Console

# 2. Run migration locally against Neon
$env:DATABASE_URL = "postgresql://..."
python -m alembic upgrade head

# 3. If successful, delete backup branch
# 4. If failed, restore from backup branch
```
