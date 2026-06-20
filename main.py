import os
import re
import html as html_mod
import threading
import time
import requests
import telebot
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CopyTextButton

# ============================================================
# FLASK — Render keep-alive
# ============================================================

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ SMS Forwarder Bot is running!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    try:
        app.run(host="0.0.0.0", port=port)
    except OSError as e:
        print(f"⚠️  Flask server failed to start (port {port} in use?): {e}")
        for fallback in [8081, 8082, 5050, 9000]:
            try:
                print(f"🔄  Trying fallback port {fallback}...")
                app.run(host="0.0.0.0", port=fallback)
                break
            except OSError:
                continue

# ============================================================
# CONFIG
# ============================================================

BOT_TOKEN      = "8428676204:AAHw7_F9lVL2Lr7zRW1FDqAc8wSJ6n5Hn6g"
CHAT_ID        = "-1003694423366"
API_KEY        = "MRKVD1UFXWP"
API_URL        = "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/console"
BOT_LINK       = "https://t.me/xpennel_bot"
CHECK_INTERVAL = 3        # seconds between polls
SMS_LIFETIME   = 21600    # 6 hours auto-delete

# ============================================================
# STATE
# ============================================================

bot = telebot.TeleBot(BOT_TOKEN)
sent_messages: list     = []   # ordered list — used for dedup + bounded trim
is_first_run: bool      = True

# ============================================================
# PREMIUM SERVICE EMOJI IDs
# ============================================================

SERVICE_EMOJI_IDS = {
    "facebook":  ("5334807341109908955", "📘"),
    "whatsapp":  ("5334759662677957452", "💬"),
    "telegram":  ("5337010556253543833", "✈️"),
    "instagram": ("5334868205091459431", "📸"),
    "tiktok":    ("5339213256001102461", "🎵"),
    "discord":   ("5116246243646898866", "🎬"),
    "twitter":   ("5215726959056662534", "🐦"),
    "snapchat":  ("5359441366554255082", "👻"),
    "viber":     ("5463060437572528782", "💜"),
    "line":      ("5399818044866327279", "🔒"),
    "signal":    ("5293998404404272267", "💬"),
    "wechat":    ("5782757599560602950", "🌟"),
    "linkedin":  ("6224222994265279792", "💼"),
    "imo":       ("5337155807752524558", "💭"),
    "google":    ("5335010201005231986", "🔍"),
    "apple":     ("5334637951894722661", "🍎"),
    "microsoft": ("5334880948259427772", "🪟"),
    "uber":      ("5298715455316303708", "🚗"),
    "paypal":    ("5776103539872896061", "💵"),
    "reddit":    ("4984421103847604984", "👽"),
    "pinterest": ("5346103513120258857", "📌"),
    "twitch":    ("5233333563306301418", "🎮"),
    "zoom":      ("5881799193219043268", "📹"),
    "netflix":   ("6255738712664050133", "🎥"),
    "spotify":   ("5411392711146095115", "🎵"),
    "skype":     ("4992613535562334989", "☎️"),
    "slack":     ("4994972469040251302", "💻"),
    "github":    ("5417836094098007862", "🐙"),
    "chatgpt":   ("5296516998996445955", "🤖"),
}

# ============================================================
# COUNTRY CODE → FLAG EMOJI + NAME
# ============================================================

COUNTRY_CODES = {
    "1":   ("🇺🇸", "USA / Canada"),      "7":   ("🇷🇺", "Russia / Kazakhstan"),
    "20":  ("🇪🇬", "Egypt"),             "27":  ("🇿🇦", "South Africa"),
    "30":  ("🇬🇷", "Greece"),            "31":  ("🇳🇱", "Netherlands"),
    "32":  ("🇧🇪", "Belgium"),           "33":  ("🇫🇷", "France"),
    "34":  ("🇪🇸", "Spain"),             "36":  ("🇭🇺", "Hungary"),
    "39":  ("🇮🇹", "Italy"),             "40":  ("🇷🇴", "Romania"),
    "41":  ("🇨🇭", "Switzerland"),       "43":  ("🇦🇹", "Austria"),
    "44":  ("🇬🇧", "United Kingdom"),    "45":  ("🇩🇰", "Denmark"),
    "46":  ("🇸🇪", "Sweden"),            "47":  ("🇳🇴", "Norway"),
    "48":  ("🇵🇱", "Poland"),            "49":  ("🇩🇪", "Germany"),
    "51":  ("🇵🇪", "Peru"),              "52":  ("🇲🇽", "Mexico"),
    "53":  ("🇨🇺", "Cuba"),              "54":  ("🇦🇷", "Argentina"),
    "55":  ("🇧🇷", "Brazil"),            "56":  ("🇨🇱", "Chile"),
    "57":  ("🇨🇴", "Colombia"),          "58":  ("🇻🇪", "Venezuela"),
    "60":  ("🇲🇾", "Malaysia"),          "61":  ("🇦🇺", "Australia"),
    "62":  ("🇮🇩", "Indonesia"),         "63":  ("🇵🇭", "Philippines"),
    "64":  ("🇳🇿", "New Zealand"),       "65":  ("🇸🇬", "Singapore"),
    "66":  ("🇹🇭", "Thailand"),          "81":  ("🇯🇵", "Japan"),
    "82":  ("🇰🇷", "South Korea"),       "84":  ("🇻🇳", "Vietnam"),
    "86":  ("🇨🇳", "China"),             "90":  ("🇹🇷", "Turkey"),
    "91":  ("🇮🇳", "India"),             "92":  ("🇵🇰", "Pakistan"),
    "93":  ("🇦🇫", "Afghanistan"),       "94":  ("🇱🇰", "Sri Lanka"),
    "95":  ("🇲🇲", "Myanmar"),           "98":  ("🇮🇷", "Iran"),
    "211": ("🇸🇸", "South Sudan"),       "212": ("🇲🇦", "Morocco"),
    "213": ("🇩🇿", "Algeria"),           "216": ("🇹🇳", "Tunisia"),
    "218": ("🇱🇾", "Libya"),             "220": ("🇬🇲", "Gambia"),
    "221": ("🇸🇳", "Senegal"),           "222": ("🇲🇷", "Mauritania"),
    "223": ("🇲🇱", "Mali"),              "224": ("🇬🇳", "Guinea"),
    "225": ("🇨🇮", "Ivory Coast"),       "226": ("🇧🇫", "Burkina Faso"),
    "227": ("🇳🇪", "Niger"),             "228": ("🇹🇬", "Togo"),
    "229": ("🇧🇯", "Benin"),             "230": ("🇲🇺", "Mauritius"),
    "231": ("🇱🇷", "Liberia"),           "232": ("🇸🇱", "Sierra Leone"),
    "233": ("🇬🇭", "Ghana"),             "234": ("🇳🇬", "Nigeria"),
    "235": ("🇹🇩", "Chad"),              "236": ("🇨🇫", "Central African Republic"),
    "237": ("🇨🇲", "Cameroon"),          "238": ("🇨🇻", "Cape Verde"),
    "239": ("🇸🇹", "Sao Tome"),          "240": ("🇬🇶", "Equatorial Guinea"),
    "241": ("🇬🇦", "Gabon"),             "242": ("🇨🇬", "Congo"),
    "243": ("🇨🇩", "DR Congo"),          "244": ("🇦🇴", "Angola"),
    "245": ("🇬🇼", "Guinea-Bissau"),     "248": ("🇸🇨", "Seychelles"),
    "249": ("🇸🇩", "Sudan"),             "250": ("🇷🇼", "Rwanda"),
    "251": ("🇪🇹", "Ethiopia"),          "252": ("🇸🇴", "Somalia"),
    "253": ("🇩🇯", "Djibouti"),          "254": ("🇰🇪", "Kenya"),
    "255": ("🇹🇿", "Tanzania"),          "256": ("🇺🇬", "Uganda"),
    "257": ("🇧🇮", "Burundi"),           "258": ("🇲🇿", "Mozambique"),
    "260": ("🇿🇲", "Zambia"),            "261": ("🇲🇬", "Madagascar"),
    "263": ("🇿🇼", "Zimbabwe"),          "264": ("🇳🇦", "Namibia"),
    "265": ("🇲🇼", "Malawi"),            "266": ("🇱🇸", "Lesotho"),
    "267": ("🇧🇼", "Botswana"),          "268": ("🇸🇿", "Eswatini"),
    "269": ("🇰🇲", "Comoros"),           "290": ("🇸🇭", "Saint Helena"),
    "291": ("🇪🇷", "Eritrea"),           "297": ("🇦🇼", "Aruba"),
    "298": ("🇫🇴", "Faroe Islands"),     "299": ("🇬🇱", "Greenland"),
    "350": ("🇬🇮", "Gibraltar"),         "351": ("🇵🇹", "Portugal"),
    "352": ("🇱🇺", "Luxembourg"),        "353": ("🇮🇪", "Ireland"),
    "354": ("🇮🇸", "Iceland"),           "355": ("🇦🇱", "Albania"),
    "356": ("🇲🇹", "Malta"),             "357": ("🇨🇾", "Cyprus"),
    "358": ("🇫🇮", "Finland"),           "359": ("🇧🇬", "Bulgaria"),
    "370": ("🇱🇹", "Lithuania"),         "371": ("🇱🇻", "Latvia"),
    "372": ("🇪🇪", "Estonia"),           "373": ("🇲🇩", "Moldova"),
    "374": ("🇦🇲", "Armenia"),           "375": ("🇧🇾", "Belarus"),
    "376": ("🇦🇩", "Andorra"),           "377": ("🇲🇨", "Monaco"),
    "378": ("🇸🇲", "San Marino"),        "380": ("🇺🇦", "Ukraine"),
    "381": ("🇷🇸", "Serbia"),            "382": ("🇲🇪", "Montenegro"),
    "383": ("🇽🇰", "Kosovo"),            "385": ("🇭🇷", "Croatia"),
    "386": ("🇸🇮", "Slovenia"),          "387": ("🇧🇦", "Bosnia"),
    "389": ("🇲🇰", "North Macedonia"),   "420": ("🇨🇿", "Czechia"),
    "421": ("🇸🇰", "Slovakia"),          "501": ("🇧🇿", "Belize"),
    "502": ("🇬🇹", "Guatemala"),         "503": ("🇸🇻", "El Salvador"),
    "504": ("🇭🇳", "Honduras"),          "505": ("🇳🇮", "Nicaragua"),
    "506": ("🇨🇷", "Costa Rica"),        "507": ("🇵🇦", "Panama"),
    "509": ("🇭🇹", "Haiti"),             "591": ("🇧🇴", "Bolivia"),
    "592": ("🇬🇾", "Guyana"),            "593": ("🇪🇨", "Ecuador"),
    "595": ("🇵🇾", "Paraguay"),          "597": ("🇸🇷", "Suriname"),
    "598": ("🇺🇾", "Uruguay"),           "670": ("🇹🇱", "Timor-Leste"),
    "673": ("🇧🇳", "Brunei"),            "675": ("🇵🇬", "Papua New Guinea"),
    "676": ("🇹🇴", "Tonga"),             "677": ("🇸🇧", "Solomon Islands"),
    "678": ("🇻🇺", "Vanuatu"),           "679": ("🇫🇯", "Fiji"),
    "680": ("🇵🇼", "Palau"),             "685": ("🇼🇸", "Samoa"),
    "686": ("🇰🇮", "Kiribati"),          "688": ("🇹🇻", "Tuvalu"),
    "689": ("🇵🇫", "French Polynesia"),  "691": ("🇫🇲", "Micronesia"),
    "692": ("🇲🇭", "Marshall Islands"),  "850": ("🇰🇵", "North Korea"),
    "852": ("🇭🇰", "Hong Kong"),         "853": ("🇲🇴", "Macau"),
    "855": ("🇰🇭", "Cambodia"),          "856": ("🇱🇦", "Laos"),
    "880": ("🇧🇩", "Bangladesh"),        "886": ("🇹🇼", "Taiwan"),
    "960": ("🇲🇻", "Maldives"),          "961": ("🇱🇧", "Lebanon"),
    "962": ("🇯🇴", "Jordan"),            "963": ("🇸🇾", "Syria"),
    "964": ("🇮🇶", "Iraq"),              "965": ("🇰🇼", "Kuwait"),
    "966": ("🇸🇦", "Saudi Arabia"),      "967": ("🇾🇪", "Yemen"),
    "968": ("🇴🇲", "Oman"),              "970": ("🇵🇸", "Palestine"),
    "971": ("🇦🇪", "UAE"),               "972": ("🇮🇱", "Israel"),
    "973": ("🇧🇭", "Bahrain"),           "974": ("🇶🇦", "Qatar"),
    "975": ("🇧🇹", "Bhutan"),            "976": ("🇲🇳", "Mongolia"),
    "977": ("🇳🇵", "Nepal"),             "992": ("🇹🇯", "Tajikistan"),
    "993": ("🇹🇲", "Turkmenistan"),      "994": ("🇦🇿", "Azerbaijan"),
    "995": ("🇬🇪", "Georgia"),           "996": ("🇰🇬", "Kyrgyzstan"),
    "998": ("🇺🇿", "Uzbekistan"),
}

# ============================================================
# PREMIUM FLAG EMOJI IDs
# ============================================================

PREMIUM_FLAGS = {
    "🇦🇩": "5911314702398396902",  "🇦🇪": "5913726554168365343",  "🇦🇫": "5913492040364068694",
    "🇦🇱": "5911357458797826163",  "🇦🇲": "5913272455866093666",  "🇦🇴": "5913753316109586411",
    "🇦🇷": "5913573356979884082",  "🇦🇹": "5911338831524664592",  "🇦🇺": "5913632326880858455",
    "🇦🇼": "5780471598922337683",  "🇦🇿": "5911197578640233518",  "🇧🇦": "5913700002680541032",
    "🇧🇩": "5911365056594973179",  "🇧🇪": "5913529642802745141",  "🇧🇫": "5913407764515786948",
    "🇧🇬": "5294329219965272288",  "🇧🇭": "5913581663446634403",  "🇧🇮": "5913766441529642752",
    "🇧🇯": "5913735869952430547",  "🇧🇳": "5911336409163109113",  "🇧🇴": "5913638795101606133",
    "🇧🇷": "5911148568768418614",  "🇧🇸": "5911451643135660214",  "🇧🇹": "5913236734623093021",
    "🇧🇼": "5911513782722499475",  "🇧🇾": "5911011185649521599",  "🇧🇿": "5913355005137522807",
    "🇨🇦": "5913623736946265914",  "🇨🇩": "5913770362834783827",  "🇨🇫": "5913443245240619222",
    "🇨🇬": "5911338788574990168",  "🇨🇭": "5913271227505448072",  "🇨🇮": "5222233374948602940",
    "🇨🇱": "5911470957603592832",  "🇨🇲": "5911172109484167745",  "🇨🇳": "5913779335021466780",
    "🇨🇴": "5913773060074246009",  "🇨🇷": "5911261745451635030",  "🇨🇺": "5431551436502611633",
    "🇨🇻": "5913571501554012193",  "🇨🇾": "5911023550860366409",  "🇨🇿": "5911198691036764307",
    "🇩🇪": "5911096835887337583",  "🇩🇯": "5911407709915190157",  "🇩🇰": "5911206009661034712",
    "🇩🇴": "5911152099231536123",  "🇩🇿": "5913782968563800236",  "🇪🇨": "5911273865849347408",
    "🇪🇪": "5910986042910969906",  "🇪🇬": "5913694831539916769",  "🇪🇷": "5433723401464198287",
    "🇪🇸": "5911193287967904547",  "🇪🇹": "5911078333168227043",  "🇫🇮": "5911041344909873378",
    "🇫🇯": "5911393832875856716",  "🇫🇲": "5911271104185373336",  "🇫🇴": "5296469342039327674",
    "🇫🇷": "5913605586414473124",  "🇬🇦": "5911037896051137264",  "🇬🇧": "5913443365499703513",
    "🇬🇩": "5913228063084121946",  "🇬🇪": "5913434771270144023",  "🇬🇭": "5913391155877252952",
    "🇬🇱": "5292014752283774878",  "🇬🇲": "5913657267755945883",  "🇬🇳": "5913471858312744319",
    "🇬🇶": "5911306279967529251",  "🇬🇷": "5911210399117611448",  "🇬🇹": "5913324858762072330",
    "🇬🇼": "5911398694778836149",  "🇬🇾": "5913579412883771480",  "🇭🇰": "5292166459118606932",
    "🇭🇳": "5911406889576436289",  "🇭🇷": "5913692684056269311",  "🇭🇹": "5913459789454643194",
    "🇭🇺": "5913767635530551104",  "🇮🇩": "5913479361620611038",  "🇮🇪": "5913440715504881532",
    "🇮🇱": "5911471936856134692",  "🇮🇳": "5913754823643107921",  "🇮🇶": "5911382442622587735",
    "🇮🇷": "5911308891307643032",  "🇮🇸": "5911047899029967246",  "🇮🇹": "5913688444923547525",
    "🇯🇲": "5913232280742006526",  "🇯🇴": "5913234136167878475",  "🇯🇵": "5913293711659241040",
    "🇰🇪": "5222279743415531561",  "🇰🇬": "5911202161370337549",  "🇰🇭": "5913368009424109643",
    "🇰🇮": "5911344698892185355",  "🇰🇲": "5913456029897678438",  "🇰🇵": "5434142701941437163",
    "🇰🇷": "5913371673905598425",  "🇰🇼": "5913290705182134003",  "🇰🇿": "5913724621433082323",
    "🇱🇦": "5913718526874489279",  "🇱🇧": "5911504273664905447",  "🇱🇮": "5911166650580734660",
    "🇱🇰": "5911293163137406640",  "🇱🇷": "5913324167272337727",  "🇱🇸": "5911059881988723711",
    "🇱🇹": "5911172315642597775",  "🇱🇺": "5913390842344640293",  "🇱🇻": "5913738489882480243",
    "🇱🇾": "5911236989260140996",  "🇲🇦": "5911482111633658301",  "🇲🇨": "5911245347266500057",
    "🇲🇩": "5913456847402045950",  "🇲🇪": "5913239436157522151",  "🇲🇬": "5913766918271012920",
    "🇲🇭": "5913235935759175692",  "🇲🇰": "5913394029210374721",  "🇲🇱": "5911305266355245916",
    "🇲🇲": "5433666360003540231",  "🇲🇳": "5911041383564580038",  "🇲🇴": "6323557758096377611",
    "🇲🇷": "5433859405898594234",  "🇲🇹": "5911023714069123567",  "🇲🇺": "5913291113204027321",
    "🇲🇻": "5913501399097806832",  "🇲🇼": "5433968339154122439",  "🇲🇽": "5913687302462246518",
    "🇲🇾": "5913654360063087453",  "🇲🇿": "5911333419865871464",  "🇳🇦": "5911108535378252443",
    "🇳🇪": "5911270086278124251",  "🇳🇬": "5911143844304393105",  "🇳🇮": "5334807849418003620",
    "🇳🇱": "5913367645226275100",  "🇳🇴": "5913617397574537046",  "🇳🇵": "5913496520014958723",
    "🇳🇿": "5913640044937089340",  "🇴🇲": "5913570801474343473",  "🇵🇦": "5913428968769327174",
    "🇵🇪": "5911207993935925780",  "🇵🇬": "5911107251183030903",  "🇵🇭": "5911268638874145162",
    "🇵🇰": "5913705895375672082",  "🇵🇱": "5913550391789752571",  "🇵🇸": "5913684768431541668",
    "🇵🇹": "5911023653939581472",  "🇵🇼": "5911283903187915549",  "🇵🇾": "5911014265141072316",
    "🇶🇦": "5911260864983339619",  "🇷🇴": "5913460373570195273",  "🇷🇸": "5913592598433369871",
    "🇷🇺": "5913274246867456342",  "🇷🇼": "5911455229433352234",  "🇸🇦": "4985897134424328239",
    "🇸🇧": "5911482712929080608",  "🇸🇨": "5911185183364616913",  "🇸🇩": "5911387497799094470",
    "🇸🇪": "5911156510162949403",  "🇸🇬": "5911531460808051849",  "🇸🇮": "5913431983836368644",
    "🇸🇰": "5913751666842145020",  "🇸🇱": "5911210450657218661",  "🇸🇲": "5913587968458625465",
    "🇸🇳": "5910995302860461643",  "🇸🇴": "5911397852965244436",  "🇸🇷": "5913275539652611719",
    "🇸🇸": "5911406262511211744",  "🇸🇹": "5913574331937462345",  "🇸🇻": "5913238624408703010",
    "🇸🇾": "5433910876786670092",  "🇸🇿": "5913374525763883286",  "🇹🇩": "5913299849167507310",
    "🇹🇬": "5913423260757790970",  "🇹🇭": "5913617968805187987",  "🇹🇯": "5911287639809463107",
    "🇹🇱": "5911141915864076479",  "🇹🇲": "5913315521503170180",  "🇹🇳": "5911332947419468671",
    "🇹🇴": "5911328226001273440",  "🇹🇷": "5910995113881901195",  "🇹🇹": "5911228635548750294",
    "🇹🇻": "5433684690923961019",  "🇹🇼": "5366187256937726720",  "🇹🇿": "5911418949844603556",
    "🇺🇦": "5911406692007941050",  "🇺🇬": "5913488939397681980",  "🇺🇸": "5913463998522592692",
    "🇺🇾": "5913623088406204470",  "🇺🇿": "5911051846104912282",  "🇻🇦": "5911211932420938860",
    "🇻🇪": "5434009132753499322",  "🇻🇳": "5913456785694736547",  "🇻🇺": "5913511535220625585",
    "🇼🇸": "5913325971158602854",  "🇽🇰": "5911433681582429010",  "🇾🇪": "5913344642189831222",
    "🇿🇦": "5911203119148044594",  "🇿🇲": "5913564754160389778",  "🇿🇼": "5911092502265336396",
}

# ============================================================
# HELPERS
# ============================================================

def get_country_info(range_num: str):
    """Returns (flag_char, country_name, flag_emoji_id)"""
    r = str(range_num).replace("+", "").replace(" ", "").strip()
    for length in [3, 2, 1]:
        prefix = r[:length]
        if prefix in COUNTRY_CODES:
            flag, name = COUNTRY_CODES[prefix]
            eid = PREMIUM_FLAGS.get(flag, "5911106310585193018")
            return flag, name, eid
    return "🌍", "Unknown", "5911106310585193018"

def get_service_emoji_html(sid: str) -> str:
    sid_l = sid.lower()
    for key, (eid, fb) in SERVICE_EMOJI_IDS.items():
        if key in sid_l:
            return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'
    return "📱"

def extract_otp(message: str) -> str:
    m = re.search(r'\b(\d{4,8})\b', message)
    return m.group(1) if m else ""

def format_otp_display(otp: str) -> str:
    if otp.isdigit() and len(otp) == 6:
        return f"{otp[:3]}-{otp[3:]}"
    return otp

# ============================================================
# AUTO DELETE
# ============================================================

def auto_delete_worker(chat_id, message_id, delay):
    time.sleep(delay)
    try:
        bot.delete_message(chat_id, message_id)
        print(f"🗑️ Auto-deleted message {message_id}")
    except Exception:
        pass

def schedule_delete(message_id):
    t = threading.Thread(
        target=auto_delete_worker,
        args=(CHAT_ID, message_id, SMS_LIFETIME),
        daemon=True
    )
    t.start()

# ============================================================
# SEND — Premium Blockquote Format
# ============================================================

def send_to_telegram(raw_message: str, range_num: str, sid: str):
    flag_char, country_name, flag_eid = get_country_info(range_num)

    flag_html = f'<tg-emoji emoji-id="{flag_eid}">{flag_char}</tg-emoji>'
    svc_html  = get_service_emoji_html(sid)
    otp_raw     = extract_otp(raw_message)
    otp_display = format_otp_display(otp_raw) if otp_raw else ""

    # Premium label emojis
    em_globe   = '<tg-emoji emoji-id="5355102594886833928">🌐</tg-emoji>'
    em_range   = '<tg-emoji emoji-id="5267295703666824255">♻️</tg-emoji>'
    em_service = '<tg-emoji emoji-id="5341715473882955310">🕹️</tg-emoji>'
    em_sms     = '<tg-emoji emoji-id="5253742260054409879">✉️</tg-emoji>'

    safe_msg = html_mod.escape(raw_message)
    text = (
        f"<blockquote>{em_globe} <b>Country:</b>  {flag_html}  {country_name}</blockquote>\n"
        f"<blockquote>{em_range} <b>Range:</b>  <code>{range_num}</code></blockquote>\n"
        f"<blockquote>{em_service} <b>Service:</b>  {svc_html}  <b>{sid.upper()}</b></blockquote>\n"
        f"<blockquote>{em_sms} <b>Full SMS:</b>  {safe_msg}</blockquote>"
    )

    markup = InlineKeyboardMarkup(row_width=2)

    # Row 1 — OTP copy (full width)
    if otp_raw:
        try:
            btn_otp = InlineKeyboardButton(
                text=f"  {otp_display}  ·  Tap to Copy",
                copy_text=CopyTextButton(text=otp_raw),
                icon_custom_emoji_id="5296369303661067030"
            )
        except Exception:
            btn_otp = InlineKeyboardButton(
                text=f"🔑  {otp_display}",
                callback_data=f"otp|{otp_raw}"
            )
        markup.add(btn_otp)

    # Row 2 — Copy Range (premium icon) | Copy Country (premium icon)
    try:
        btn_rang = InlineKeyboardButton(
            text="  Copy Range",
            copy_text=CopyTextButton(text=str(range_num)),
            icon_custom_emoji_id="5267295703666824255",
            style="primary"
        )
    except Exception:
        btn_rang = InlineKeyboardButton(
            text="📋  Copy Range",
            callback_data=f"rang|{range_num}",
            style="primary"
        )

    try:
        btn_country = InlineKeyboardButton(
            text="  Copy Country",
            copy_text=CopyTextButton(text=f"{flag_char} {country_name}"),
            icon_custom_emoji_id="5355102594886833928",
            style="primary"
        )
    except Exception:
        btn_country = InlineKeyboardButton(
            text="🌐  Copy Country",
            callback_data=f"ctry|{country_name}",
            style="primary"
        )

    markup.row(btn_rang, btn_country)

    # Row 3 — NUMBER BOT (premium bot-logo icon, danger/red)
    try:
        btn_bot = InlineKeyboardButton(
            text="  NUMBER BOT",
            url=BOT_LINK,
            icon_custom_emoji_id="4943094697238201446",
            style="danger"
        )
    except Exception:
        btn_bot = InlineKeyboardButton(
            text="🤖  NUMBER BOT",
            url=BOT_LINK
        )
    markup.add(btn_bot)

    # ── Send with flood-protection retry ────────────────────
    for attempt in range(3):
        try:
            sent = bot.send_message(
                CHAT_ID,
                text,
                parse_mode="HTML",
                reply_markup=markup
            )
            schedule_delete(sent.message_id)
            print(f"✅ Sent | {sid.upper()} | {range_num} | {country_name} | OTP: {otp_raw or 'N/A'}")
            return True
        except telebot.apihelper.ApiTelegramException as e:
            err = str(e)
            if "Too Many Requests" in err or "retry after" in err.lower():
                m2 = re.search(r"retry after (\d+)", err, re.IGNORECASE)
                wait = int(m2.group(1)) + 2 if m2 else 30
                print(f"⚠️  Flood — waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"❌  Send error: {e}")
                return False
        except Exception as e:
            print(f"❌  Send error: {e}")
            return False
    return False

# ============================================================
# CALLBACK HANDLER
# ============================================================

@bot.callback_query_handler(func=lambda c: True)
def cb_handler(call):
    try:
        d = call.data
        if d.startswith("otp|"):
            otp = d.split("|", 1)[1]
            bot.answer_callback_query(call.id,
                text=f"🔑 OTP: {format_otp_display(otp)}", show_alert=True)
        elif d.startswith("rang|"):
            rang = d.split("|", 1)[1]
            bot.answer_callback_query(call.id,
                text=f"📋 Range: {rang}", show_alert=True)
        elif d.startswith("ctry|"):
            ctry = d.split("|", 1)[1]
            bot.answer_callback_query(call.id,
                text=f"🌐 Country: {ctry}", show_alert=True)
    except Exception:
        pass

# ============================================================
# MAIN POLLING LOOP
# ============================================================

def main():
    global is_first_run
    print("🚀 Bot started — syncing existing messages...")

    while True:
        start = time.time()
        try:
            headers = {"mauthapi": API_KEY, "Cache-Control": "no-cache"}
            params  = {"_": int(time.time() * 1000)}
            res  = requests.get(API_URL, headers=headers, params=params, timeout=30)
            data = res.json()

            if data.get("meta", {}).get("status") == "ok":
                hits = data.get("data", {}).get("hits", [])

                for hit in reversed(hits):
                    msg_time = hit.get("time")
                    if msg_time in sent_messages:
                        continue

                    if is_first_run:
                        sent_messages.append(msg_time)
                        continue

                    raw_msg  = hit.get("message", "")
                    range_n  = str(hit.get("range", ""))
                    sid      = str(hit.get("sid", "Unknown"))

                    ok = send_to_telegram(raw_msg, range_n, sid)
                    if ok:
                        sent_messages.append(msg_time)
                    else:
                        print(f"⚠️  Failed to forward range: {range_n}")

                if is_first_run:
                    print("✅ Sync complete. Listening for new messages...")
                    is_first_run = False

        except Exception as e:
            print(f"⚠️  Poll error: {e}")

        # Trim oldest entries first (list preserves insertion order)
        if len(sent_messages) > 2000:
            del sent_messages[:1000]

        elapsed   = time.time() - start
        sleep_for = max(0, CHECK_INTERVAL - elapsed)
        time.sleep(sleep_for)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    # Flask server (background) — Render keep-alive
    threading.Thread(target=run_server, daemon=True).start()

    # Bot polling (background) — Telegram callback handler
    threading.Thread(
        target=lambda: bot.infinity_polling(none_stop=True),
        daemon=True
    ).start()

    # Main SMS loop (foreground)
    main()
