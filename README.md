# UO Athletics — Transformational Prospect Intelligence

**Forever Ducks Major Gift Pipeline | Confidential**

This system automatically searches the web every day to find University of Oregon
alumni with the capacity to make $5 million or more in philanthropic gifts to
University of Oregon Athletics.

## What It Does

- **Daily at 8:00 AM Pacific**: An AI research agent searches the internet for UO alumni
  with significant wealth and philanthropic capacity
- **Automatically updates** a live web dashboard with detailed prospect profiles
- **Optionally emails you** a daily notification with a link to new findings
- **Grows over time**: The database accumulates and refreshes prospects daily, organized
  by giving capacity tier

## Prospect Tiers

| Tier | Capacity | Description |
|------|----------|-------------|
| Tier 1 · Transformational | $25M+ | Naming rights, endowments, facility gifts |
| Tier 2 · Principal | $10M–$25M | Major program endowments |
| Tier 3 · Major Gift | $5M–$10M | Priority giving capacity |

## Setup (One-Time — 5 Minutes)

You only need to do this once. After that, everything runs automatically.

### Step 1: Add Your Anthropic API Key

1. Go to the **Settings** tab of this GitHub repository
2. Click **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `ANTHROPIC_API_KEY`
5. Value: Your Anthropic API key (from console.anthropic.com)

### Step 2: Enable GitHub Pages (Your Live Dashboard)

1. Go to **Settings** → **Pages**
2. Under "Source", select **Deploy from a branch**
3. Branch: **`claude/amazing-thompson-r33Wp`** (or `main` once merged), folder: **`/docs`**
4. Click **Save**
5. Your dashboard will be live at: `https://riisg.github.io/uoa-transformation-prospects/`

### Step 3 (Optional): Set Up Email Notifications

To receive a daily email when new prospects are found:

1. In **Secrets and variables** → **Actions**, add these secrets:
   - `NOTIFICATION_EMAIL` — your email address (e.g., `riisgonzales@yahoo.com`)
   - `SMTP_USERNAME` — your Gmail address
   - `SMTP_PASSWORD` — your [Gmail App Password](https://myaccount.google.com/apppasswords)

### Step 4: Run It Now (Optional)

To get your first results immediately without waiting until tomorrow morning:

1. Go to the **Actions** tab
2. Click **Daily UO Prospect Research**
3. Click **Run workflow** → **Run workflow**

Results will appear on your dashboard within 5 minutes.

---

*CONFIDENTIAL — University of Oregon Athletics · Forever Ducks Program*
