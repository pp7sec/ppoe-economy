# PoE Economy Discord Bot

สคริปต์โพสต์สรุปราคา PoE1 / PoE2 ลง Discord อัตโนมัติ (poedb.tw / poe2db.tw)  
รองรับ emoji แยกภาค และ config ย้ายเซิร์ฟเวอร์ได้โดยไม่ต้องแก้โค้ด

> บอทจะลบข้อความเก่าของตัวเองแล้วโพสต์ใหม่ทุกครั้ง (มี marker ล่องหน) — รันซ้ำกี่ทีก็ไม่สแปม

---

## ไฟล์ในแพ็ค

```
.
├── economy_poe1.py              # PoE1 (poedb.tw) — 21 รายการ
├── economy_poe2.py              # PoE2 (poe2db.tw) — 22 รายการ
├── emoji_config.json            # 👈 แก้เลข emoji ตรงนี้ถ้าย้ายเซิร์ฟ
├── requirements.txt
├── .gitignore
├── README.md
└── .github/workflows/economy.yml  # cron บน GitHub Actions
```

## emoji_config.json

ย้ายเซิร์ฟใหม่ → อัพ emoji เข้าเซิร์ฟใหม่ → Copy ID → แก้ไฟล์นี้อย่างเดียว ไม่ต้องแก้โค้ด

```json
{
  "poe1": {
    "chaos": "<:chaos1:100000000000000001>",
    "divine": "<:divine1:100000000000000002>",
    "exalted": "<:exalted1:100000000000000003>"
  },
  "poe2": {
    "chaos": "<:chaos2:200000000000000001>",
    "divine": "<:divine2:200000000000000002>",
    "exalted": "<:exalted2:200000000000000003>"
  }
}
```

- `poe1` ใช้ `chaos1/divine1/exalted1` — โพสต์ลงห้อง PoE1
- `poe2` ใช้ `chaos2/divine2/exalted2` — โพสต์ลงห้อง PoE2

สคริปต์จะอ่านไฟล์นี้ตอนรัน ถ้าไม่มีไฟล์จะ fallback เป็นค่า default เดิม (ไม่พัง)

วิธีหา ID emoji: ใน Discord พิมพ์ `\:chaos1:` แล้วส่ง จะได้ `<:chaos1:เลข>` หรือคลิกขวา emoji → Copy ID (ต้องเปิด Developer Mode)

---

## วิธีใช้แบบ Local / Cron บนเครื่อง

```bash
pip install -r requirements.txt
# หรือ: pip install requests beautifulsoup4

export DISCORD_BOT_TOKEN="MTM3OD..."
export DISCORD_SELF_ID="333333333333333333"   # ป้องกันลบผิดบอท
export TARGET_CHANNEL="111111111111111111"     # poe1: 111111111111111111, poe2: 222222222222222222
python economy_poe1.py
python economy_poe2.py
```

ตั้ง cron ทุกชั่วโมง:
```cron
0 * * * *  cd /path/to/repo && DISCORD_BOT_TOKEN=... DISCORD_SELF_ID=... TARGET_CHANNEL=111111111111111111 python economy_poe1.py >> /tmp/poe1.log 2>&1
0 * * * *  cd /path/to/repo && DISCORD_BOT_TOKEN=... DISCORD_SELF_ID=... TARGET_CHANNEL=222222222222222222 python economy_poe2.py >> /tmp/poe2.log 2>&1
```

---

## วิธีใช้บน GitHub Actions (แนะนำ Private repo)

### 1. สร้าง repo (ติ๊ก Private ปลอดภัยสุด)

### 2. ใส่ Secrets

`Settings` → `Secrets and variables` → `Actions` → `New repository secret`:

| Name | Value |
|------|-------|
| `DISCORD_BOT_TOKEN` | token บอท `MTM3OD...` (ห้าม hardcode ในไฟล์!) |
| `DISCORD_SELF_ID` | `333333333333333333` |

> Public repo ก็ใช้ Secrets ได้ (เข้ารหัสด้วย libsodium, log เบลอเป็น `***`) แต่ Private ปลอดภัยกว่า — log ใครก็ดูได้ใน public

### 3. Push ไฟล์ทั้งหมดขึ้น repo

Workflow `.github/workflows/economy.yml` จะรันเองทุกชั่วโมง (UTC)

แก้เวลา: `cron: '0 * * * *'` = ทุกชั่วโมงตรง, `*/30 * * * *` = ทุก 30 นาที, `0 0 * * *` = 07:00 ไทย

กดรันมือ: `Actions` → `poe-economy` → `Run workflow`

---

## วิธีหา Channel ID / Bot ID

- **Channel ID:** Discord Settings → Advanced → Developer Mode → คลิกขวาห้อง → Copy Channel ID
- **Bot ID:** `curl -H "Authorization: Bot <TOKEN>" https://discord.com/api/v10/users/@me` ดูฟิลด์ `id`

## สิทธิ์ที่บอทต้องมีในห้อง

- View Channel, Send Messages
- Manage Messages (ไว้ลบข้อความเก่าตัวเอง — ไม่มีก็โพสต์ได้แต่จะสะสม)

## พฤติกรรมลบข้อความเก่า

ลบเฉพาะข้อความที่ (1) เป็น bot และ (2) มี marker ล่องหนของตัวเอง (`\u200b\u200b` สำหรับ poe1, `\u200b\u200b\u200b` สำหรับ poe2) → ไม่ลบของคนอื่น/บอทอื่น

---

## License

MIT — ใช้ได้ตามสบาย
