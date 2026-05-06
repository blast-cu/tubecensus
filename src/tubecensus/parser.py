
import re
from glob import glob
from bs4 import BeautifulSoup
import json
from jsonpath_ng.ext import parse
import os
import cdx_toolkit.myrequests as myr #myrequests_get

SUBSCRIBER_TERMS = [
    # English
    "subscriber", "subscribers",
    # German
    "Abonnent", "Abonnenten",
    # Dutch
    "abonnee", "abonnees",
    # French
    "abonné", "abonnés",
    # Swedish
    "prenumerant", "prenumeranter",
    # Norwegian/Danish
    "abonnent", "abonnenter",
    # Finnish
    "tilaaja", "tilaajaa",
    # Estonian
    "tellijat",
    # Lithuanian
    "prenumeratorių",
    # Czech
    "odběratel", "odběratelé", "odběratelů",
    # Polish
    "subskrybentów", "subskrypcji",
    # Hungarian
    "feliratkozó",
    # Romanian
    "de abonați",
    # Portuguese
    "inscrito", "inscritos", "subscritores",
    # Spanish
    "suscriptor", "suscriptores",
    # Italian
    "iscritti",
    # Russian
    "подписчик", "подписчика", "подписчиков",
    # Ukrainian
    "користувач", "користувачі", "користувачів", "Підписався", "Підписалося","підписалися",
    # Bulgarian
    "абонати",
    # Kazakh
    "жазылушы",
    # Greek
    "εγγεγραμμένοι",
    # Georgian
    "გამომწერი",
    # Turkish
    "abone",
    # Azerbaijani
    "abunəçi",
    # Arabic
    "مشترك", "مشتركين", "مشتركًا", "واحد", "مشتركان",
    # Urdu
    "سبسکرائبرز",
    # Vietnamese
    "người đăng ký",
    # Indonesian/Malay
    "pelanggan",
    # Thai
    "คน","ผู้ติดตาม",
    # Nepali
    "सदस्यहरू",
    # Bangla
    "জন সদস্য",
    # Sinhala
    "ග්‍රාහකයන්",
    # Korean
    "명", "구독자",
    # Japanese
    "人", "チャンネル登録者数",
    # Chinese
    "位訂閱者", '訂閱人數',
    # Swahili
    "wanafuatilia",
]

def get_id(html,ts):
    js_pattern = re.compile(r"""yt\.setConfig\(\s*['"]CHANNEL_ID['"]\s*,\s*['"]([a-zA-Z0-9_-]+)['"]\s*\)""")
    meta_pattern = re.compile(r"""<meta\s+itemprop\s*=\s*['"]channelId['"]\s+content\s*=\s*['"]([a-zA-Z0-9_-]+)['"]""")
    canonical_pattern = re.compile(r"""<link\s+rel\s*=\s*['"]canonical['"]\s+href\s*=\s*['"]https?://(?:www\.)?youtube\.com/channel/([a-zA-Z0-9_-]+)['"]""")
    yt_init_pattern = re.compile(r'"urlCanonical"\s*:\s*".*?youtube\.com/channel/([a-zA-Z0-9_-]+)"')
    m = js_pattern.search(html)
    if m:
        if len(m.group(1)) == 24 and m.group(1).startswith("UC"):
            return m.group(1)df
        elif len(m.group(1)) == 22:
            return "UC"+m.group(1)
    else:
        m = meta_pattern.search(html)
        if m:
            if len(m.group(1)) == 24 and m.group(1).startswith("UC"):
                return m.group(1)
            elif len(m.group(1)) == 22:
                return "UC"+m.group(1)
        else:
            m = canonical_pattern.search(html)
            if m:
                return m.group(1)
            else:
                m = yt_init_pattern.search(html)
                if m:
                    return m.group(1)
                else:
                    return None

def get_username(html,ts):
    if int(str(ts[:4])) in range(2012,2021):
        person = re.compile(r'<span(?=[^>]*itemprop\s*=\s*[\'"]author[\'"])(?=[^>]*itemtype\s*=\s*[\'"][^\'"]*schema\.org/Person[\'"])[^>]*>.*?youtube\.com/user/([a-zA-Z0-9_-]+).*?</span>', re.DOTALL)
        m = person.search(html)
        if m:
            return m.group(1).lower()
    return None

def parse_space_makers(soup):
    for sm in soup.find_all(class_="spaceMaker"):
        if sm.find("span", class_="profileTitles") and any(term in sm.find("span", class_="profileTitles").get_text().lower() for term in SUBSCRIBER_TERMS):
            return str(sm).split("</span>")[1].split("<br")[0].strip().replace(',','')

def parse_stat_box1s(soup, usr):
    stats_box = soup.find("div", id="statsBox")
    if stats_box:
        link = stats_box.find("a", href=True)
        if link:
            href = link["href"]
            if "add_user="  in href:
                add_user = href.split("add_user=")[-1]
                add_user = add_user.split("&")[0].split("/")[0]
                if add_user.lower() == usr.lower():
                    for strong in stats_box.find_all("strong"):
                        if "Subscribers:" in strong.get_text():
                            next_text = strong.next_sibling
                            if next_text:
                                sub_str = next_text.strip().rstrip("</a></strong>")
                                sub_str = sub_str.split("<")[0].strip().replace(",", "")
                                return sub_str
    return None

def parse_stat_box2s(soup, usr):
    for s in soup.find_all("table", class_="statsBox")+soup.find_all("div", class_="statsBox")+[soup.find("div", id="statsBox")]:
        if s:
            for a in s.find_all("a", href=True):
                href = a["href"]
                if "user=" not in href:
                    continue
                link_user = href.split("user=")[-1].split("&")[0].split("/")[0]
                if link_user.lower() != usr.lower():
                    continue
                return a.get_text(strip=True).replace(",", "")
    return None

def parse_box3s(soup, usr):
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "view=subscribers" in href and "user=" in href:
            link_user = href.split("user=")[-1].split("&")[0].split("/")[0]
            if link_user.lower() == usr.lower():
                sub_str = a.get_text(strip=True).replace(",", "")
                return sub_str

    return None

def parse_small_texts(soup):
    texts=soup.find_all(class_="smallText")
    for t in texts:
        if t.name=="span":
            if any (term in t.get_text().lower() for term in SUBSCRIBER_TERMS):
                if t.find_next_sibling("b"):
                    return t.find_next_sibling("b").get_text().replace(',','')
                elif t.find_next_sibling("strong"):
                    return t.find_next_sibling("strong").get_text().replace(',','')
        elif t.name=='div':
            if any (term in t.get_text().lower() for term in SUBSCRIBER_TERMS):
                strongs=t.find_all("strong")+t.find_all("b")
                if len(strongs)>1:
                    raise Exception(f"Multiple strong/b tags found in smallText div: {[s.get_text() for s in strongs]}")
                for s in strongs:
                    return s.get_text().replace(',','')
    #backup in case of non-english failure
    if len(soup.find_all(id='user-profile-subscriber-count'))>1:
        raise Exception("Multiple elements with id user-profile-subscriber-count found.")
    for tz in soup.find_all(id='user-profile-subscriber-count'):
        return tz.get_text().replace(',','')
    return None

def parse_counts(soup):
    for s in soup.find_all(id="user-profile-subscriber-count"):
        return s.get_text().replace(',','')
    for s in soup.find_all(id="profile_show_subscriber_count"):
        return s.get_text().replace(',','')
    for s in soup.find_all(name="channel-box-item-count"):
        if s['href'].endswith("view=subscribers"):
            return s.get_text().replace(',','')
    return None

def parse_stat_entries(soup):
    for s in soup.find_all(class_="stat-entry"):
        if s.find("span", class_="stat-name") and any(term in s.find("span", class_="stat-name").get_text().lower() for term in SUBSCRIBER_TERMS):
            return s.find("span", class_="stat-value").get_text().replace(',','')
    return None

def parse_buttons(soup, id):
    for b in soup.find_all("button", attrs={"data-channel-external-id": id})+soup.find_all("button", attrs={"data-subscription-value": id}):
        if b.has_attr("data-subscriber-count-tooltip"):
            return b.get("title")
        s=b.find_next_sibling('span')
        if s and any("subscri" in (cls.lower() if cls else "") for cls in s.get("class", [])):
            if s.get('aria-label'):
                return s.get('aria-label')
            return s.get_text()
        if 'yt-uix-button-subscription-container' in b.parent.get('class', []):
            for y in b.parent.find_all('span', class_='yt-subscription-button-subscriber-count-branded-horizontal'):
                if y.get('aria-label'):
                    return y.get('aria-label')
                return y.get_text()
    return None

def parse_initial_data(html):
    match = re.search(
        r'(?:var\s+ytInitialData|window\["ytInitialData"\])\s*=\s*({.*?});\s*(?:</script>|$)',
        html,
        re.DOTALL | re.MULTILINE
    )

    if match:
        data = json.loads(match.group(1))
        matches = parse('$..subscriberCountText').find(data)
        ms=[(match.full_path, match.value) for match in matches]
        hdrs=set()
        for i in ms:
            if 'header' in str(i[0]):
                if 'simpleText' in i[1]:
                    hdrs.add(i[1]['simpleText'])
                elif 'runs' in i[1] and len(i[1]['runs'])==1 and 'text' in i[1]['runs'][0]:
                    hdrs.add(i[1]['runs'][0]['text'])
        if len(hdrs):
            return sorted(list(hdrs),key=lambda x: len(x))[-1]
    return None 

def parse_url(url):
    # to-do: add profile?user= with other arguments in between
    m = re.search(r"youtube\.com/(profile\?user=|user/|channel/|c/|@)([a-zA-Z0-9_-]+)", url)
    if m:
        prefix = m.group(1)
        value = m.group(2)
        if prefix in ("profile?user=", "user/"):
            return "username", value
        elif prefix == "channel/":
            return "id", value
        elif prefix == "c/":
            return "custom", value
        elif prefix == "@":
            return "handle", value
    return None

def parse_wb(url, ts):
    html = myr.myrequests_get(url)
    try:
        content = str(html.text)
    except:
        return None
    if not html or not content or len(content)<100:
        return None
    soup = BeautifulSoup(content, "html.parser")
    metadata = {
        "username":get_username(content,ts) or None,
        "id":get_id(content,ts) or None,
        "custom":None,
        "handle":None,
        "subs":None,
        "ts":ts,
        "url":url
    }
    if parse_url(url):
        metadata[parse_url(url)[0]]=parse_url(url)[1]
    metadata["subs"] = parse_initial_data(content) or parse_buttons(soup, metadata["id"] or "") or parse_stat_entries(soup) or parse_counts(soup) or parse_small_texts(soup) or parse_box3s(soup, metadata["username"] or "")  or parse_stat_box2s(soup, metadata["username"] or "") or parse_stat_box1s(soup, metadata["username"] or "") or parse_space_makers(soup)
    if metadata['subs']==None:
        return None
    return metadata
