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

## ตัวแปรที่ใช้ (Environment variables)

| ตัวแปร | จำเป็น | คืออะไร / มีไว้ทำไม |
|--------|:------:|---------------------|
| `DISCORD_BOT_TOKEN` | ✅ | **token ของบอท** ใช้ยืนยันตัวกับ Discord API — เป็นความลับสูงสุด **ห้าม hardcode / ห้าม commit** ให้ใส่ผ่าน env หรือ GitHub Secrets เท่านั้น |
| `TARGET_CHANNEL` | ✅ | **ID ห้องปลายทาง** ที่จะให้บอทโพสต์ (ใส่หลายห้องได้ คั่นด้วย `,`) — PoE1/PoE2 คนละห้องกัน |
| `DISCORD_SELF_ID` | แนะนำ | **ID ของบอทตัวเอง** (Bot's own user ID) — ดูหัวข้อด้านล่าง |

### `DISCORD_SELF_ID` คืออะไร?

คือ **ID ของตัวบอทเอง** (ไม่ใช่ token, ไม่ใช่ ID ห้อง)

**ทำงานยังไง:** ทุกครั้งก่อนโพสต์ราคาใหม่ บอทจะลบโพสต์เก่าของตัวเองทิ้งก่อน เพื่อไม่ให้สแปมสะสม โดยจะลบเฉพาะข้อความที่เข้าเงื่อนไขครบ:

1. เป็นข้อความจาก bot (ไม่ใช่คน)
2. มี marker ล่องหนของสคริปต์นี้ (`​​` สำหรับ poe1, `​​​` สำหรับ poe2)
3. **และถ้า set `DISCORD_SELF_ID` ไว้** → ต้องเป็น ID ของบอทตัวนี้เท่านั้น

**มีไว้ทำไม:** เป็นตัว "กันลบผิดบอท" — ถ้าในห้องเดียวกันมีบอทหลายตัวและบังเอิญใช้ marker ตรงกัน การ set ค่านี้จะทำให้บอทลบเฉพาะโพสต์ของ **ตัวเอง** เท่านั้น ไม่ไปแตะของบอทอื่น

**ถ้าไม่ set:** บอทจะลบข้อความ bot ตัวไหนก็ได้ที่มี marker ตรงกัน (ปกติใช้งานได้ แต่เสี่ยงลบผิดถ้ามีหลายบอท) — ดูโค้ดที่ `economy_poe1.py` ฟังก์ชัน `delete_old_messages()`

**หาค่าได้ยังไง:** ดูหัวข้อ [วิธีหา Channel ID / Bot ID](#วิธีหา-channel-id--bot-id) ด้านล่าง

---

## วิธีใช้แบบ Local / Cron บนเครื่อง

```bash
pip install -r requirements.txt
# หรือ: pip install requests beautifulsoup4

export DISCORD_BOT_TOKEN="MTM3OD..."
export DISCORD_SELF_ID="333333333333333333"   # ID ของบอทเอง — กันลบโพสต์ผิดบอท (แนะนำให้ใส่)
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

### 2. ใส่ Secrets และ Variables

ไปที่ `Settings` → `Secrets and variables` → `Actions` — หน้านี้มี **2 แท็บ**:

**แท็บ `Secrets`** (ค่าเข้ารหัส, log โชว์เป็น `***`) → กด `New repository secret`:

| Name | Value |
|------|-------|
| `DISCORD_BOT_TOKEN` | token บอท `MTM3OD...` (ห้าม hardcode ในไฟล์!) |
| `DISCORD_SELF_ID` | ID ของบอทเอง `333333333333333333` — กันลบโพสต์ผิดบอท (ดูหัวข้อ [ตัวแปรที่ใช้](#ตัวแปรที่ใช้-environment-variables)) |

**แท็บ `Variables`** (ค่าธรรมดา ไม่ลับ) → กด `New repository variable`:

| Name | Value |
|------|-------|
| `TARGET_CHANNEL_POE1` | Channel ID ห้อง PoE1 |
| `TARGET_CHANNEL_POE2` | Channel ID ห้อง PoE2 |

> **ทำไม Channel ID อยู่แท็บ Variables ไม่ใช่ Secrets?** เพราะ Channel ID ไม่ใช่ความลับ ใส่เป็น Variable ก็พอ (แก้ได้ในหน้า Settings ที่เดียว ไม่ต้องแตะโค้ด) — workflow จะอ่านค่านี้ผ่าน `${{ vars.TARGET_CHANNEL_POE1 }}` ให้อัตโนมัติ
>
> วิธีหา Channel ID → คลิกขวาที่ห้อง → `Copy Channel ID` (ดูหัวข้อ [วิธีหา Channel ID / Bot ID](#วิธีหา-channel-id--bot-id))

> Public repo ก็ใช้ Secrets ได้ (เข้ารหัสด้วย libsodium, log เบลอเป็น `***`) แต่ Private ปลอดภัยกว่า — log ใครก็ดูได้ใน public

### 3. Push ไฟล์ทั้งหมดขึ้น repo

Workflow `.github/workflows/economy.yml` จะรันเองทุกชั่วโมง (UTC)

แก้เวลา: `cron: '0 * * * *'` = ทุกชั่วโมงตรง, `*/30 * * * *` = ทุก 30 นาที, `0 0 * * *` = 07:00 ไทย

> ⚠️ **cron แก้ได้ในไฟล์ `economy.yml` เท่านั้น — ใส่ Variables ไม่ได้** GitHub Actions อ่านส่วน `on.schedule` ก่อนโหลด context ของ vars/secrets ค่าตรงนั้นจึงต้องเป็นข้อความตายตัว ถ้าใส่ `${{ vars.CRON }}` schedule จะไม่ทำงาน (ต่างจาก Channel ID ที่ย้ายไป Variables ได้)

กดรันมือ: `Actions` → `poe-economy` → `Run workflow`

---

## วิธีหา Channel ID / Bot ID

ก่อนอื่นเปิด **Developer Mode**: Discord `Settings` → `Advanced` → เปิด `Developer Mode` (จะมีเมนู Copy ID โผล่ตอนคลิกขวา)

- **Channel ID:** คลิกขวาที่ห้อง → `Copy Channel ID`
- **Bot ID (`DISCORD_SELF_ID`):** คลิกขวาที่ชื่อบอท (ในรายชื่อสมาชิก หรือที่โพสต์ของบอท) → `Copy User ID`

> ทางเลือก (ไม่ต้องเปิด Developer Mode): `curl -H "Authorization: Bot <TOKEN>" https://discord.com/api/v10/users/@me` แล้วดูฟิลด์ `id`

## สิทธิ์ที่บอทต้องมีในห้อง

- View Channel, Send Messages
- Manage Messages (ไว้ลบข้อความเก่าตัวเอง — ไม่มีก็โพสต์ได้แต่จะสะสม)

## พฤติกรรมลบข้อความเก่า

ลบเฉพาะข้อความที่ (1) เป็น bot และ (2) มี marker ล่องหนของตัวเอง (`\u200b\u200b` สำหรับ poe1, `\u200b\u200b\u200b` สำหรับ poe2) → ไม่ลบของคนอื่น/บอทอื่น

---

## License

MIT — ใช้ได้ตามสบาย
