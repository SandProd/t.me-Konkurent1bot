import requests
import gzip
import brotli
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

url = "https://new.busk.website/hot/call.php"
headers = {
    "Cookie": "_fbp=fb.1.1734529035075.618096322771607895",
    "Cache-Control": "max-age=0",
    "Sec-Ch-Ua": '"Not?A_Brand";v="99", "Chromium";v="130"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Linux"',
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://new.busk.website",
    "Content-Type": "application/x-www-form-urlencoded",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Referer": "https://new.busk.website/hot/",
    "Accept-Encoding": "gzip, deflate, br"
}
data = {
    "name": "123",
    "phone": "+380000000000",
    "utm_source": "",
    "utm_medium": "",
    "utm_term": "",
    "utm_content": "",
    "utm_campaign": "",
    "utm_podmeni_zag": "",
    "comment": "nospam"
}

try:
    logging.info("Sending POST request to the server.")
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()  # Raises HTTPError for bad responses (4xx and 5xx)
    logging.info("Request sent successfully. Status code: %s", response.status_code)

    content = None
    encoding = response.headers.get("Content-Encoding", "").lower()
    logging.info("Content-Encoding received: %s", encoding)

    # Handle GZIP
    if "gzip" in encoding:
        try:
            logging.info("Attempting GZIP decompression.")
            content = gzip.decompress(response.content).decode("utf-8")
            logging.info("GZIP decompression successful.")
        except Exception as e:
            logging.error("GZIP decompression failed: %s", e)
            raise RuntimeError("GZIP decompression failed") from e

    # Handle Brotli
    elif "br" in encoding:
        try:
            logging.info("Attempting Brotli decompression.")
            content = brotli.decompress(response.content).decode("utf-8")
            logging.info("Brotli decompression successful.")
        except Exception as e:
            logging.error("Brotli decompression failed: %s", e)
            logging.info("Falling back to interpreting response as plain text.")
            content = response.content.decode("utf-8")  # Attempt plain text as a fallback

    # Fallback to plain text
    else:
        logging.info("No compression detected, using plain text response.")
        content = response.text

    logging.info("Request processing completed successfully.")
    print("Request successful!")
    print(content)

except requests.exceptions.RequestException as e:
    logging.error("An error occurred during the request: %s", e)
    print("An error occurred during the request:")
    print(e)
except RuntimeError as e:
    logging.error("A decompression error occurred: %s", e)
    print("A decompression error occurred:")
    print(e)
except Exception as e:
    logging.error("An unexpected error occurred: %s", e)
    print("An unexpected error occurred:")
    print(e)