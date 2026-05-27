import os
import threading
from flask import Flask

# --- FLASK SERVER SETUP FOR RENDER (ADDED BY MINOX AUTO SETUP) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is successfully running on Render!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

import requests
import time
import html

# --- আপনার কনফিগারেশন ---
BOT_TOKEN = "8708045547:AAER7gCS-IhbrdV_pcZV_UtxqqPgxdw28rA"
CHAT_ID = "-1003694423366"  
API_KEY = "MRKVD1UFXWP"     
API_URL = "https://2oo9.cloud/api/MXS47FLFX0U/project/tetragonexvoltxsms/@public/api/console"
CHECK_INTERVAL = 1       

sent_messages = set()
is_first_run = True  # প্রথমবার পুরনো মেসেজগুলো ইগনোর করার জন্য

# পৃথিবীর প্রায় সব দেশের কলিং কোড ও পতাকার ডিকশনারি
COUNTRY_CODES = {
    "1": "🇺🇸/🇨🇦 USA/Canada", "7": "🇷🇺/🇰🇿 Russia/Kazakhstan", "20": "🇪🇬 Egypt", 
    "27": "🇿🇦 South Africa", "30": "🇬🇷 Greece", "31": "🇳🇱 Netherlands", "32": "🇧🇪 Belgium", 
    "33": "🇫🇷 France", "34": "🇪🇸 Spain", "36": "🇭🇺 Hungary", "39": "🇮🇹 Italy", 
    "40": "🇷🇴 Romania", "41": "🇨🇭 Switzerland", "43": "🇦🇹 Austria", "44": "🇬🇧 United Kingdom", 
    "45": "🇩🇰 Denmark", "46": "🇸🇪 Sweden", "47": "🇳🇴 Norway", "48": "🇵🇱 Poland", 
    "49": "🇩🇪 Germany", "51": "🇵🇪 Peru", "52": "🇲🇽 Mexico", "53": "🇨🇺 Cuba", 
    "54": "🇦🇷 Argentina", "55": "🇧🇷 Brazil", "56": "🇨🇱 Chile", "57": "🇨🇴 Colombia", 
    "58": "🇻🇪 Venezuela", "60": "🇲🇾 Malaysia", "61": "🇦🇺 Australia", "62": "🇮🇩 Indonesia", 
    "63": "🇵🇭 Philippines", "64": "🇳🇿 New Zealand", "65": "🇸🇬 Singapore", "66": "🇹🇭 Thailand", 
    "81": "🇯🇵 Japan", "82": "🇰🇷 South Korea", "84": "🇻🇳 Vietnam", "86": "🇨🇳 China", 
    "90": "🇹🇷 Turkey", "91": "🇮🇳 India", "92": "🇵🇰 Pakistan", "93": "🇦🇫 Afghanistan", 
    "94": "🇱🇰 Sri Lanka", "95": "🇲🇲 Myanmar", "98": "🇮🇷 Iran", "211": "🇸🇸 South Sudan", 
    "212": "🇲🇦 Morocco", "213": "🇩🇿 Algeria", "216": "🇹🇳 Tunisia", "218": "🇱🇾 Libya", 
    "220": "🇬🇲 Gambia", "221": "🇸🇳 Senegal", "222": "🇲🇷 Mauritania", "223": "🇲🇱 Mali", 
    "224": "🇬🇳 Guinea", "225": "🇨🇮 Ivory Coast", "226": "🇧🇫 Burkina Faso", "227": "🇳🇪 Niger", 
    "228": "🇹🇬 Togo", "229": "🇧🇯 Benin", "230": "🇲🇺 Mauritius", "231": "🇱🇷 Liberia", 
    "232": "🇸🇱 Sierra Leone", "233": "🇬🇭 Ghana", "234": "🇳🇬 Nigeria", "235": "🇹🇩 Chad", 
    "236": "🇨🇫 Central African Republic", "237": "🇨🇲 Cameroon", "238": "🇨🇻 Cape Verde", 
    "239": "🇸🇹 Sao Tome and Principe", "240": "🇬🇶 Equatorial Guinea", "241": "🇬🇦 Gabon", 
    "242": "🇨🇬 Congo", "243": "🇨🇩 DR Congo", "244": "🇦🇴 Angola", "245": "🇬🇼 Guinea-Bissau", 
    "246": "🇮🇴 Diego Garcia", "247": "🇦🇨 Ascension Island", "248": "🇸🇨 Seychelles", 
    "249": "🇸🇩 Sudan", "250": "🇷🇼 Rwanda", "251": "🇪🇹 Ethiopia", "252": "🇸🇴 Somalia", 
    "253": "🇩🇯 Djibouti", "254": "🇰🇪 Kenya", "255": "🇹🇿 Tanzania", "256": "🇺🇬 Uganda", 
    "257": "🇧🇮 Burundi", "258": "🇲🇿 Mozambique", "260": "🇿🇲 Zambia", "261": "🇲🇬 Madagascar", 
    "262": "🇷🇪 Reunion", "263": "🇿🇼 Zimbabwe", "264": "🇳🇦 Namibia", "265": "🇲🇼 Malawi", 
    "266": "🇱🇸 Lesotho", "267": "🇧🇼 Botswana", "268": "🇸🇿 Eswatini", "269": "🇰🇲 Comoros", 
    "290": "🇸🇭 Saint Helena", "291": "🇪🇷 Eritrea", "297": "🇦🇼 Aruba", "298": "🇫🇴 Faroe Islands", 
    "299": "🇬🇱 Greenland", "350": "🇬🇮 Gibraltar", "351": "🇵🇹 Portugal", "352": "🇱🇺 Luxembourg", 
    "353": "🇮🇪 Ireland", "354": "🇮🇸 Iceland", "355": "🇦🇱 Albania", "356": "🇲🇹 Malta", 
    "357": "🇨🇾 Cyprus", "358": "🇫🇮 Finland", "359": "🇧🇬 Bulgaria", "370": "🇱🇹 Lithuania", 
    "371": "🇱🇻 Latvia", "372": "🇪🇪 Estonia", "373": "🇲🇩 Moldova", "374": "🇦🇲 Armenia", 
    "375": "🇧🇾 Belarus", "376": "🇦🇩 Andorra", "377": "🇲🇨 Monaco", "378": "🇸🇲 San Marino", 
    "380": "🇺🇦 Ukraine", "381": "🇷🇸 Serbia", "382": "🇲🇪 Montenegro", "383": "🇽🇰 Kosovo", 
    "385": "🇭🇷 Croatia", "386": "🇸🇮 Slovenia", "387": "🇧🇦 Bosnia and Herzegovina", 
    "389": "🇲🇰 North Macedonia", "420": "🇨🇿 Czech Republic", "421": "🇸🇰 Slovakia", 
    "423": "🇱🇮 Liechtenstein", "500": "🇫🇰 Falkland Islands", "501": "🇧🇿 Belize", 
    "502": "🇬🇹 Guatemala", "503": "🇸🇻 El Salvador", "504": "🇭🇳 Honduras", "505": "🇳🇮 Nicaragua", 
    "506": "🇨🇷 Costa Rica", "507": "🇵🇦 Panama", "508": "🇵🇲 Saint Pierre and Miquelon", 
    "509": "🇭🇹 Haiti", "590": "🇬🇵 Guadeloupe", "591": "🇧🇴 Bolivia", "592": "🇬🇾 Guyana", 
    "593": "🇪🇨 Ecuador", "594": "🇬🇫 French Guiana", "595": "🇵🇾 Paraguay", "596": "🇲🇶 Martinique", 
    "597": "🇸🇷 Suriname", "598": "🇺🇾 Uruguay", "599": "🇨🇼 Curacao", "670": "🇹🇱 East Timor", 
    "672": "🇦🇶 Antarctica", "673": "🇧🇳 Brunei", "674": "🇳🇷 Nauru", "675": "🇵🇬 Papua New Guinea", 
    "676": "🇹🇴 Tonga", "677": "🇸🇧 Solomon Islands", "678": "🇻🇺 Vanuatu", "679": "🇫🇯 Fiji", 
    "680": "🇵🇼 Palau", "681": "🇼🇫 Wallis and Futuna", "682": "🇨🇰 Cook Islands", "683": "🇳🇺 Niue", 
    "685": "🇼🇸 Samoa", "686": "🇰🇮 Kiribati", "687": "🇳🇨 New Caledonia", "688": "🇹🇻 Tuvalu", 
    "689": "🇵🇫 French Polynesia", "690": "🇹🇰 Tokelau", "691": "🇫🇲 Micronesia", "692": "🇲🇭 Marshall Islands", 
    "850": "🇰🇵 North Korea", "852": "🇭🇰 Hong Kong", "853": "🇲🇴 Macau", "855": "🇰🇭 Cambodia", 
    "856": "🇱🇦 Laos", "880": "🇧🇩 Bangladesh", "886": "🇹🇼 Taiwan", "960": "🇲🇻 Maldives", 
    "961": "🇱🇧 Lebanon", "962": "🇯🇴 Jordan", "963": "🇸🇾 Syria", "964": "🇮🇶 Iraq", 
    "965": "🇰🇼 Kuwait", "966": "🇸🇦 Saudi Arabia", "967": "🇾🇪 Yemen", "968": "🇴🇲 Oman", 
    "970": "🇵🇸 Palestine", "971": "🇦🇪 UAE", "972": "🇮🇱 Israel", "973": "🇧🇭 Bahrain", 
    "974": "🇶🇦 Qatar", "975": "🇧🇹 Bhutan", "976": "🇲🇳 Mongolia", "977": "🇳🇵 Nepal", 
    "992": "🇹🇯 Tajikistan", "993": "🇹🇲 Turkmenistan", "994": "🇦🇿 Azerbaijan", "995": "🇬🇪 Georgia", 
    "996": "🇰🇬 Kyrgyzstan", "998": "🇺🇿 Uzbekistan"
}

def get_country_info(range_num):
    range_str = str(range_num)
    for length in [3, 2, 1]:
        prefix = range_str[:length]
        if prefix in COUNTRY_CODES:
            return COUNTRY_CODES[prefix]
    return "🌐 Unknown"

def get_console_data():
    headers = {
        "mauthapi": API_KEY,
        "Cache-Control": "no-cache"
    }
    params = {
        "_": int(time.time() * 1000) 
    }
    try:
        response = requests.get(API_URL, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("meta", {}).get("status") == "ok":
                return data.get("data", {}).get("hits", [])
        else:
            print(f"❌ API Error: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Network Error: {e}")
    return []

# country_name_only আর্গুমেন্টটি এখানে রিসিভ করা হচ্ছে
def send_to_telegram(text, range_num, country_name_only):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # ইনলাইন কীবোর্ডে এখন ফ্ল্যাগ ছাড়া শুধু দেশের নাম কপি হবে
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "Copy Range", "copy_text": {"text": str(range_num)}},
                {"text": "Copy Country", "copy_text": {"text": str(country_name_only)}}
            ],
            [{"text": "Developer 👤", "url": "https://t.me/rahi455"}]
        ]
    }
    
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": reply_markup
    }
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Request Error: {e}")
        return False

def main():
    global is_first_run
    print("Bot is running... Syncing existing messages...")
    
    while True:
        start_time = time.time()
        
        hits = get_console_data()
        
        for hit in reversed(hits):
            msg_time = hit.get("time")
            
            if msg_time not in sent_messages:
                if is_first_run:
                    sent_messages.add(msg_time)
                else:
                    raw_message = hit.get("message", "N/A")
                    range_num = hit.get("range", "N/A")
                    sid = hit.get("sid", "N/A")
                    
                    safe_message = html.escape(raw_message)
                    country_info = get_country_info(range_num)
                    
                    # ফ্ল্যাগ ও দেশের নাম আলাদা করা হচ্ছে (প্রথম স্পেসের পরের অংশটুকু দেশের নাম)
                    country_name_only = country_info.split(" ", 1)[1] if " " in country_info else country_info
                    
                    formatted_msg = (
                        f"<blockquote>🌐 Country: {country_info}</blockquote>\n"
                        f"<blockquote>♻️ Range: <code>{range_num}</code></blockquote>\n"
                        f"<blockquote>🕹️ Service: {sid}</blockquote>\n"
                        f"<blockquote>✉️ Full SMS: {safe_message}</blockquote>"
                    )
                    
                    # send_to_telegram এ country_name_only পাঠানো হচ্ছে
                    if send_to_telegram(formatted_msg, range_num, country_name_only):
                        sent_messages.add(msg_time)
                        print(f"✅ Fast Forwarded Range: {range_num}")
                    else:
                        print(f"⚠️ Failed to forward Range: {range_num}")
        
        if is_first_run:
            print("✅ Sync complete. Monitoring for NEW messages every 1 seconds...")
            is_first_run = False
            
        if len(sent_messages) > 1000:
            sent_messages.clear()
            
        elapsed_time = time.time() - start_time
        sleep_time = max(0, CHECK_INTERVAL - elapsed_time)
        time.sleep(sleep_time)

if __name__ == "__main__":
    # --- Start Flask Server in Background ---
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    main()
