import pandas as pd
import requests
import pandas

BASE_URL = "https://api.mangadex.org"


def get_manga(title):
    response = requests.get(
        BASE_URL + "/manga",
        params={"title": title}
    )
    return response.json()


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
    print(total)

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
    df = get_full_feed(manga_id)
    formatted_df = df.copy()

    formatted_df = formatted_df.rename(columns={"attributes.volume": "volume", "attributes.chapter": "chapter",
                                                "attributes.translatedLanguage": "language",
                                                "attributes.pages": "pages",
                                                "attributes.title": "title"
                                                })

    new_df = pandas.DataFrame()
    for index, row in formatted_df.iterrows():
        row["group"] = row["relationships"][0]["id"]
        row = row.to_frame()
        row = row.transpose()
        new_df = pandas.concat([new_df, pandas.DataFrame(row)])
    new_df = new_df.drop(
        columns=["attributes.readableAt", "attributes.publishAt", "attributes.createdAt", "attributes.updatedAt",
                 "attributes.externalUrl", "attributes.version", "relationships"])
    new_df["chapter"] = new_df["chapter"].astype(float)
    group_counts = new_df["group"].value_counts()

    new_df["group"] = pandas.Categorical(new_df["group"], categories=group_counts.index, ordered=True)
    new_df = new_df.sort_values(by=["chapter", "group"], ascending=[True, True])

    chapter_list = []
    chapters_df = pandas.DataFrame()

    for index, row in new_df.iterrows():
        if row["chapter"] not in chapter_list:
            chapter_list.append(row["chapter"])
            chapters_df = pandas.concat([chapters_df, pandas.DataFrame(row).transpose()])

    print(chapters_df)
    return chapters_df
