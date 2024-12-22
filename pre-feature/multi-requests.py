import requests
import logging
import gzip
import brotli
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def send_post_request(url, headers, data):
    try:
        logging.info("Sending POST request to %s", url)
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        logging.info("Request sent successfully to %s. Status code: %s", url, response.status_code)

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
                content = response.content.decode("utf-8")

        # Fallback to plain text
        else:
            logging.info("No compression detected, using plain text response.")
            content = response.text

        logging.info("Request to %s completed successfully.", url)
        return f"Request to {url} successful. Content: {content[:100]}..."  # Log first 100 characters of response

    except requests.exceptions.RequestException as e:
        logging.error("An error occurred during the request to %s: %s", url, e)
        return f"Error occurred during request to {url}: {e}"

# Adding all requests to the requests_data list
requests_data = [
    # First request
    {
        "url": "https://www.mytopmarket.space/order1.php",
        "headers": {
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Content-Type": "multipart/form-data; boundary=----WebKitFormBoundaryKWapP6NKs39WaaMv",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.140 Safari/537.36",
        },
        "data": (
            "------WebKitFormBoundaryKWapP6NKs39WaaMv\r\n"
            "Content-Disposition: form-data; name=\"comment\"\r\n\r\n42-48\r\n"
            "------WebKitFormBoundaryKWapP6NKs39WaaMv\r\n"
            "Content-Disposition: form-data; name=\"name\"\r\n\r\n123\r\n"
            "------WebKitFormBoundaryKWapP6NKs39WaaMv\r\n"
            "Content-Disposition: form-data; name=\"phone\"\r\n\r\n+38 (000) 000 00 00\r\n"
            "------WebKitFormBoundaryKWapP6NKs39WaaMv--\r\n"
        ),
    },
    # Second request
    {
        "url": "https://www.cossmik.com.ua/",
        "headers": {
            "Cookie": "PHPSESSID=a04822721d429656b2ed2ca440601790; _fbp=fb.2.1734703688591.51932804780617507",
            "Content-Type": "multipart/form-data; boundary=----WebKitFormBoundarydtPQqW4oQEkdBu5B",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.140 Safari/537.36",
        },
        "data": (
            "------WebKitFormBoundarydtPQqW4oQEkdBu5B\r\n"
            "Content-Disposition: form-data; name=\"itemID\"\r\n\r\n7268\r\n"
            "------WebKitFormBoundarydtPQqW4oQEkdBu5B\r\n"
            "Content-Disposition: form-data; name=\"CurPrice\"\r\n\r\n299\r\n"
            "------WebKitFormBoundarydtPQqW4oQEkdBu5B--\r\n"
        ),
    },
    # Third request
    {
        "url": "https://kolgotki.tv-shop.online/thank-you.php",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.140 Safari/537.36",
        },
        "data": "comment=42-48&name=aaa&phone=%2B38+%28000%29+000+00+00",
    },
    # Fourth request
    {
        "url": "https://www.mytopmarket.space/order1.php",
        "headers": {
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Content-Type": "multipart/form-data; boundary=----WebKitFormBoundarykXujEuH6qBAYxmGs",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.140 Safari/537.36",
        },
        "data": (
            "------WebKitFormBoundarykXujEuH6qBAYxmGs\r\n"
            "Content-Disposition: form-data; name=\"product-id\"\r\n\r\n407\r\n"
            "------WebKitFormBoundarykXujEuH6qBAYxmGs--\r\n"
        ),
    },
    # Fifth request
    {
        "url": "https://www.mytopmarket.space/order1.php",
        "headers": {
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Content-Type": "multipart/form-data; boundary=----WebKitFormBoundarymGWK5mDww9PPABA6",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.140 Safari/537.36",
        },
        "data": (
            "------WebKitFormBoundarymGWK5mDww9PPABA6\r\n"
            "Content-Disposition: form-data; name=\"comment\"\r\n\r\n42-48|299|405\r\n"
            "------WebKitFormBoundarymGWK5mDww9PPABA6--\r\n"
        ),
    },
]

# Execute requests in parallel
with ThreadPoolExecutor() as executor:
    futures = [
        executor.submit(send_post_request, req["url"], req["headers"], req["data"])
        for req in requests_data
    ]

    # Gather and print results
    for future in futures:
        print(future.result())