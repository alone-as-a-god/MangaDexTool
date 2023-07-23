from concurrent.futures import ThreadPoolExecutor

import requests
import pandas
import os
import threading
from functools import partial
from PIL import Image
from pypdf import PdfMerger

BASE_URL = "https://api.mangadex.org"
MAX_THREADS = 20  # more than 20 threads will cause chapters to be skipped for some reason


def get_mangas(title):
    response = requests.get(
        BASE_URL + "/manga",
        params={"title": title}
    )
    return response.json()["data"]


def get_full_feed(manga_id):
    limit = 100
    offset = 0

    response = requests.get(
        BASE_URL + f"/manga/{manga_id}/feed",
        params={"translatedLanguage[]": "en",
                "order[chapter]": "asc",
                "offset": offset,
                }
    )
    data = response.json()
    total = data["total"]
    df = pandas.json_normalize(data["data"])
    offset += limit

    while total > offset:
        response = requests.get(
            BASE_URL + f"/manga/{manga_id}/feed",
            params={"translatedLanguage[]": "en",
                    "order[chapter]": "asc",
                    "offset": offset,
                    }
        )
        data = response.json()
        temp = pandas.json_normalize(data["data"])
        df = pandas.concat([df, temp])
        offset += limit

    return df


def get_chapters(manga_id):
    feed_df = get_full_feed(manga_id)

    feed_df = feed_df.rename(columns={"attributes.volume": "volume",  # Rename columns to make them more readable
                                      "attributes.chapter": "chapter",
                                      "attributes.translatedLanguage": "language",
                                      "attributes.pages": "pages",
                                      "attributes.title": "title"
                                      })

    new_df = pandas.DataFrame()
    for index, row in feed_df.iterrows():  # Extract group id from relationships (rest is not needed)
        row["group"] = row["relationships"][0]["id"]
        row = row.to_frame()
        row = row.transpose()
        new_df = pandas.concat([new_df, pandas.DataFrame(row)])
    new_df = new_df.drop(  # Drop columns that are not needed
        columns=["attributes.readableAt",
                 "attributes.publishAt",
                 "attributes.createdAt",
                 "attributes.updatedAt",
                 "attributes.externalUrl",
                 "attributes.version",
                 "relationships"
                 ])
    new_df["chapter"] = new_df["chapter"].astype(float)  # Convert chapter to float so it can be sorted
    group_counts = new_df["group"].value_counts()  # Sort groups by number of chapters uploaded

    new_df["group"] = pandas.Categorical(new_df["group"], categories=group_counts.index,
                                         ordered=True)  # Sort groups by chapter, place higher chapter groups first
    new_df = new_df.sort_values(by=["chapter", "group"], ascending=[True, True])

    chapter_list = []
    chapters_df = pandas.DataFrame()

    for index, row in new_df.iterrows():
        if row["chapter"] not in chapter_list:
            chapter_list.append(row["chapter"])
            chapters_df = pandas.concat([chapters_df, pandas.DataFrame(row).transpose()])

    chapters_df = chapters_df.reset_index(drop=True)
    return chapters_df


def get_images(chapter_id, title, chapter):
    print(f"Downloading {title} chapter {chapter}...")
    response = requests.get(BASE_URL + f"/at-home/server/{chapter_id}")
    r = response.json()
    base_url = r["baseUrl"]
    chapter_hash = r["chapter"]["hash"]
    data = r["chapter"]["data"]  # high quality

    if chapter % 1 == 0:
        chapter = int(chapter)

    os.makedirs(f"images/{title}/{chapter}", exist_ok=True)

    i = 0
    for page in data:
        r = requests.get(f"{base_url}/data/{chapter_hash}/{page}")
        file_name = str(i) + "." + page.split(".")[-1]
        with open(f"images/{title}/{chapter}/{file_name}", "wb") as f:
            f.write(r.content)
        i += 1

    print("Downloaded " + str(len(data)) + " pages")
    create_pdf(title, chapter)


def get_all_images(chapters, title):
    executor = ThreadPoolExecutor(max_workers=MAX_THREADS)
    partial_get_images = partial(get_images, title=title)

    executor.map(get_images, chapters["id"], [title] * len(chapters), chapters["chapter"])
    executor.shutdown(wait=True)


def create_pdf(title, chapter):
    print(f"Creating pdf for {title} chapter {chapter}...")
    os.makedirs(f"pdf/{title}/by_chapter", exist_ok=True)
    if chapter % 1 == 0:
        chapter = int(chapter)
    path = f"images/{title}/{chapter}"

    if not os.path.exists(path) or len(os.listdir(path)) == 0:
        print("No images found")
        return

    images = []

    # try:
    for file in os.listdir(path):
        if file.endswith((".jpg", ".png", ".jpeg", ".gif")):
            images.append(Image.open(os.path.join(path, file)))

    images.sort(key=lambda x: int(x.filename.split("/")[-1].split(".")[0]))
    print(images)
    images[0].save(f"pdf/{title}/by_chapter/{chapter}.pdf", save_all=True, append_images=images[1:])
    # except:
    # print("Error creating pdf at " + path)


def pdf_combine(title):
    os.makedirs(f"pdf/{title}/combined", exist_ok=True)
    path = f"pdf/{title}/by_chapter/"

    if not os.path.exists(path) or len(os.listdir(path)) == 0:
        print("No chapters found")
        return

    pdfs = []
    for file in os.listdir(path):
        if file.endswith(".pdf"):
            pdfs.append(file)

    pdfs.sort()
    print(pdfs)
    merger = PdfMerger()
    for pdf in pdfs:
        merger.append(path + pdf)

    merger.write(f"pdf/{title}/{title}_combined.pdf")
    merger.close()
