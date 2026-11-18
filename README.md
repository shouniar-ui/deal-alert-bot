# Deal Alert Bot: setup guide (no coding needed)

This bot runs for free on GitHub every 15 minutes. Each time it checks deal feeds,
keeps the deals that match your niche and price limit, and posts new ones to your
Telegram channel and/or Discord server. It never posts the same deal twice.
Setup takes about 30 minutes.

---

## Step 1: Make your channel (pick one or both)

**Telegram (recommended: the most popular app for deal channels)**
1. In Telegram, tap the pencil icon, choose **New Channel**, give it a name
   (e.g. "Tech Deals Daily"), make it **Public**, and pick a link like `t.me/techdealsdaily`.
2. Message **@BotFather**, send `/newbot`, and follow the prompts.
   It gives you a **token** (looks like `123456:ABC-xyz...`). Copy it somewhere safe.
3. Open your channel, go to **Admins → Add Admin**, search for your bot's username, and add it
   with permission to post messages.
4. Your **chat ID** is your channel's link name with an @ in front, e.g. `@techdealsdaily`.

**Discord**
1. In your server, open a channel's settings, then **Integrations → Webhooks → New Webhook**.
2. Click **Copy Webhook URL**.

## Step 2: Put the bot on GitHub

1. Make a free account at github.com.
2. Click **+ → New repository**. Name it `deal-alert-bot`, choose **Public**
   (public repos get unlimited free running time; your passwords stay hidden either way),
   and click **Create repository**.
3. Click **uploading an existing file**, drag in these files, and click **Commit changes**:
   `bot.py`, `config.yaml`, `my_deals.csv`, `requirements.txt`, `README.md`
4. Click **Add file → Create new file**. In the name box type exactly:
   `.github/workflows/deals.yml`
   Open `deals.yml` from the download in any text editor (TextEdit or Notepad), copy all of it,
   paste it into the big box, and click **Commit changes**.

## Step 3: Add your secret keys

In your repo, go to **Settings → Secrets and variables → Actions → New repository secret**.
Add each one you need (the name must match exactly):

| Name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | the token from BotFather |
| `TELEGRAM_CHAT_ID` | `@yourchannelname` |
| `DISCORD_WEBHOOK_URL` | the webhook URL (only if using Discord) |
| `AMAZON_TAG` | your Amazon Associates tag, e.g. `yourname-20` (optional, see Step 6) |

## Step 4: Turn it on and test it

1. Go to **Settings → Actions → General**, under **Workflow permissions** choose
   **Read and write permissions**, and click **Save**.
2. Click the **Actions** tab. If asked, click **I understand my workflows, go ahead and enable them**.
3. Click **Deal alerts → Run workflow → Run workflow**.
4. After about a minute you should see a green check, and deals should appear in your channel.
   On the first run it posts only the newest few and skips older ones, so it doesn't flood your channel.
   If you see a red X, click it to read the error (usually a mistyped secret name).

From then on it runs on its own every 15 minutes.

## Step 5: Choose your niche

Click `config.yaml`, then the **pencil icon**, edit, and **Commit changes**. You can change:
- `include_keywords`: the words a deal must contain (your niche)
- `exclude_keywords`: the words to skip
- `max_price`: the most a deal can cost
- `max_posts_per_run`: the most deals posted every 15 minutes

A focused niche ("Gaming deals under $100", "Baby deals for new parents") grows faster
than a general deals channel, because people know exactly why to join.

## Step 6: Making money

The Slickdeals links in the feed earn **Slickdeals** the commission, not you.
They're there to keep your channel busy and growing. You earn money in these ways:

1. **Your own affiliate deals:** Sign up for Amazon Associates (affiliate-program.amazon.com)
   and add your tag as the `AMAZON_TAG` secret. To feature a deal, open `my_deals.csv`, click the pencil, and add a line:
   `Echo Dot $22 lowest price ever,https://www.amazon.com/dp/B0DCCNHWV5`
   It's posted once with a ⭐ and your tag. Any direct Amazon link from a feed also gets your tag.
   Two minutes a day of adding your best finds is where most of the money comes from.
2. **Sponsored posts:** Once you have a few thousand members, brands pay to be featured.
3. **Paid VIP channel:** Charge $3–5/month for a second channel with the best deals or earlier alerts.

Always keep the "may earn us a commission" footer. The FTC requires it, and so does Amazon.

## Good to know

- **Feed terms:** Slickdeals' content belongs to Slickdeals. Before you make money from the channel,
  read their terms of use, or replace their feeds in `config.yaml` with other sources.
- **GitHub pauses inactive schedules:** If the bot ever stops, open **Actions → Deal alerts**
  and click **Enable workflow**.
- **Pause the bot:** Go to **Actions → Deal alerts → ⋯ → Disable workflow**.
