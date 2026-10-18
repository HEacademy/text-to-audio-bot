# Telegram Text-to-Audio Bot (Python)

Այս բոտը Telegram-ում ստանում է տեքստ, ElevenLabs API-ով ստեղծում է MP3 խոսք և հետ ուղարկում աուդիոն։ Կարող է արտասանել հայերեն։ Բոտը սովորական հեռախոսազանգ չի կատարում։

## Ինչ է պետք

- Python 3.10 կամ ավելի նոր տարբերակ
- Telegram բոտի token՝ ստացիր Telegram-ի `@BotFather`-ից (`/newbot`)
- ElevenLabs API key և Voice ID
- Ինտերնետ կապ

## Windows-ում գործարկում

1. ZIP-ը բացիր մի թղթապանակում։
2. Տեղադրիր Python 3.10+։ Տեղադրման ժամանակ նշիր **Add Python to PATH**։
3. Կրկնակի սեղմիր `install_windows.bat`։
4. Նույն պանակում պատճենիր `.env.example` ֆայլը և պատճենի անունը փոխիր `.env`։ Եթե Windows-ը ֆայլի ընդլայնումը թաքցնում է, համոզվիր, որ անունը վերջանում է `.env`, ոչ թե `.env.txt`։
5. `.env` ֆայլում լրացրու՝
   - `TELEGRAM_BOT_TOKEN` — BotFather-ի token-ը
   - `ELEVENLABS_API_KEY` — ElevenLabs API key-ը
   - `ELEVENLABS_VOICE_ID` — ElevenLabs-ի ընտրած ձայնի ID-ն
6. Դատարկ թող `ALLOWED_TELEGRAM_USER_IDS`-ը, պահպանիր `.env`-ը և առաջին անգամ գործարկիր `run_windows.bat`։
7. Telegram-ում բացիր բոտը և ուղարկիր `/id`։ Բոտը կպատասխանի քո թվային Telegram ID-ով։
8. Փակի՛ր բոտի պատուհանը։ `.env` ֆայլում տեղադրիր այդ թիվը `ALLOWED_TELEGRAM_USER_IDS=`-ի կողքին։ Պահպանիր ֆայլը։ Մի քանի օգտատեր ավելացնելու համար ID-ները բաժանիր ստորակետով։
9. Նորից գործարկիր `run_windows.bat`, Telegram-ում ուղարկիր `/start`, հետո գրիր տեքստ։

## Python հրամաններով գործարկում

Թղթապանակի ներսում բացիր Terminal կամ PowerShell և գործարկիր՝

```bash
python -m venv .venv
```

Windows-ում ակտիվացրու միջավայրը՝

```powershell
.venv\Scripts\Activate.ps1
```

Տեղադրիր կախվածությունները և գործարկիր՝

```bash
pip install -r requirements.txt
python bot.py
```

Նախքան գործարկումը լրացրու `.env` ֆայլը։

## GitHub և Cloudflare

- GitHub-ը կարող է պահել նախագծի կոդը։ **`.env` ֆայլը մի վերբեռնիր GitHub**․ `.gitignore`-ն այն բաց է թողնում։
- Այս տարբերակը սովորական Python ծրագիր է և աշխատում է polling-ով։ Cloudflare Workers-ը դրա համար պետք չէ։
- Եթե բոտը գործարկես քո համակարգչում, այն կաշխատի միայն մինչ համակարգիչն ու բոտի պատուհանը միացված են։ Մշտական աշխատանքի համար պետք է Python ծրագիր գործարկող հոսթինգ։

## Խնդիրների արագ ստուգում

- `Բացակայում են .env կարգավորումները` — լրացրու նշված արժեքները։
- Telegram-ից պատասխան չկա — ստուգիր token-ը և համոզվիր, որ `run_windows.bat`-ի պատուհանը բաց է։
- ElevenLabs-ի սխալ — ստուգիր API key-ը, Voice ID-ն, հաշվի քվոտան և մոդելի հասանելիությունը։
- Հայերեն արտասանությունը — Voice ID-ն փոխիր հայերենին համապատասխանող ձայնով։

## Անվտանգություն

- Երբեք մի ուղարկիր bot token-ը կամ ElevenLabs API key-ը ուրիշներին և մի տեղադրիր դրանք հանրային repository-ում։
- Սկզբնական կարգավորմամբ բոտից կարող է օգտվել միայն այն Telegram ID-ն, որը նշված է `.env`-ի `ALLOWED_TELEGRAM_USER_IDS` դաշտում։
- API-ների օգտագործումը կարող է ծախսել ElevenLabs հաշվի քվոտան։
