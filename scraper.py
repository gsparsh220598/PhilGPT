import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

download_dir = "./source_documents/"
url = "https://www.sacred-texts.com/hin/index.htm"
url_prefix = "https://www.sacred-texts.com/hin/"
# Send GET request to the URL
response = requests.get(url)

# Parse the HTML content
soup = BeautifulSoup(response.content, "html.parser", from_encoding="utf-8")

# Find all span elements with class "c_t"
span_elements = soup.find_all("span", class_="c_t")

# Extract the href values
hrefs = pd.Series([span.a["href"] for span in span_elements if span.a])
urls = hrefs.apply(lambda x: url_prefix + x)
#filter only .htm files
urls = urls[hrefs.str.contains(".htm")]
#filter links with index.htm
urls_indices = urls[urls.str.contains("index")].reset_index(drop=True)
# urls_noindices = urls[~urls.str.contains("index")].reset_index(drop=True)
# # Print the extracted href values
# for url in urls_noindices:
#     response = requests.get(url)
#     file_name = os.path.join(download_dir, url.split("/")[-1])
#     with open(file_name, "wb") as f:
#         f.write(response.content)

#     print(f"Downloaded: {file_name}")

for url in urls_indices:
    print(url)

def get_hrefs(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser", from_encoding="utf-8")
    a_elements = soup.find_all("a")
    hrefs = pd.Series([a["href"] for a in a_elements if a["href"]])
    hrefs = hrefs[~hrefs.str.contains("/")]
    return hrefs

# failed_urls = []
# for url in urls_indices[2:  ]:
#     try:
#         url_prefix_1 = url.split("index.htm")[0]
#         hrefs = get_hrefs(url)
#         new_urls = hrefs.apply(lambda x: url_prefix_1 + x).to_list()
#         for new_url in new_urls:
#             hrefs = get_hrefs(new_url)
#             hrefs = hrefs[~hrefs.str.contains("index")].reset_index(drop=True)
#             nested_urls = hrefs.apply(lambda x: url_prefix_1 + x).to_list()
#             #remove urls in nested_urls that contain urls in new_urls
#             nested_urls = [nested_url for nested_url in nested_urls if nested_url not in new_urls]
#             for nested_url in nested_urls:
#                 r3 = requests.get(nested_url)
#                 file_name = os.path.join(download_dir, nested_url.split("/")[-2], nested_url.split("/")[-1])
#                 if not os.path.exists(os.path.dirname(file_name)):
#                     os.mkdir(os.path.dirname(file_name))
#                 with open(file_name, "wb") as f:
#                     f.write(r3.content)

#                 print(f"Downloaded: {file_name}")
#     except:
#         failed_urls.append(url)
#         print(f"Failed: {url}")


# print(len(failed_urls))
