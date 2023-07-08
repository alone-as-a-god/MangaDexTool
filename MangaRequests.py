import requests
import pandas

BASE_URL = "https://api.mangadex.org"


def get_manga(title):
    response = requests.get(
        BASE_URL + "/manga",
        params={"title": title}
    )
    return response.json()


def get_chapters(manga_id):
    response = requests.get(
        BASE_URL + f"/manga/{manga_id}/feed",
        params={"translatedLanguage[]": "en",
                "order[chapter]": "asc"
                }
    )
    data = pandas.DataFrame(response.json()["data"])
    grouped_data = data.groupby(data["relationships"].apply(lambda x: x[0]["id"]))

    return response.json()
