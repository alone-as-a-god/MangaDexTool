import requests
import pandas
import os
from PIL import Image
from pypdf import PdfMerger

BASE_URL = "https://api.mangadex.org"


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
    response = requests.get(BASE_URL + f"/at-home/server/{chapter_id}")
    r = response.json()
    base_url = r["baseUrl"]
    chapter_hash = r["chapter"]["hash"]
    data = r["chapter"]["data"]  # high quality

    os.makedirs(f"images/{title}/{chapter}", exist_ok=True)

    for page in data:
        r = requests.get(f"{base_url}/data/{chapter_hash}/{page}")
        with open(f"images/{title}/{chapter}/{page}", "wb") as f:
            f.write(r.content)

    print("Downloaded " + str(len(data)) + " pages.")


def create_pdf(title, chapter):
    os.makedirs(f"pdf/{title}", exist_ok=True)
    path = f"images/{title}/{chapter}"

    if not os.path.exists(path) or len(os.listdir(path)) == 0:
        print("No images found")
        return

    images = []
    for file in os.listdir(path):
        if file.endswith(".jpg"):
            images.append(Image.open(os.path.join(path, file)))

    images[0].save(f"pdf/{title}/{chapter}.pdf", save_all=True, append_images=images[1:])


def pdf_combine(title):
    os.makedirs(f"pdf/{title}/combined", exist_ok=True)
    path = f"pdf/by_chapter/{title}"
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

    merger.write(f"pdf/{title}/combined/{title}_combined.pdf")
    merger.close()
