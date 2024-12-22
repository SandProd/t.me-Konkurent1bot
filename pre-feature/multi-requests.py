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

# Example request data
requests_data = [
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
    # Add more request data here
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