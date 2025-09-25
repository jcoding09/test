import os
import requests
import re

INPUT_URL = os.getenv("M3U_URL")  # from GitHub Secret
OUTPUT_FILE = "ott-jstar.m3u"

def clean_entry(block: str) -> str:
    lines = block.strip().splitlines()
    if not lines or not lines[0].startswith("#EXTINF"):
        return ""

    extinf = lines[0]
    license_key = ""
    user_agent = ""
    cookie = ""
    url = ""

    for line in lines[1:]:
        if line.startswith("#KODIPROP:inputstream.adaptive.license_key="):
            license_key = line
        elif line.startswith("#EXTVLCOPT:http-user-agent="):
            user_agent = line.split("=", 1)[1].strip()
        elif line.startswith("#EXTHTTP:"):
            m = re.search(r'"cookie":"([^"]+)"', line)
            if m:
                cookie = m.group(1)
        elif line.startswith("http"):
            url = line.strip()

    url = re.sub(r"&xxx=.*", "", url)

    if url:
        headers = []
        if user_agent:
            headers.append(f"user-agent={user_agent}")
        if cookie:
            headers.append(f"cookie={cookie}")
        if headers:
            url = url + "|" + "&".join(headers)

    out_lines = [extinf]
    if license_key:
        out_lines.append("#KODIPROP:inputstream.adaptive.license_type=clearkey")
        out_lines.append(license_key)
    if url:
        out_lines.append(url)

    return "\n".join(out_lines)

def main():
    if not INPUT_URL:
        raise ValueError("M3U_URL is not set! Add it as a GitHub Secret.")

    print("Fetching M3U from secret INPUT_URL...")
    r = requests.get(INPUT_URL)
    r.raise_for_status()
    raw_text = r.text

    blocks = raw_text.split("#EXTINF")
    cleaned_blocks = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        entry = clean_entry("#EXTINF" + block)
        if entry:
            cleaned_blocks.append(entry)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("\n\n".join(cleaned_blocks))

    print(f"Generated {OUTPUT_FILE} with {len(cleaned_blocks)} channels.")

if __name__ == "__main__":
    main()
