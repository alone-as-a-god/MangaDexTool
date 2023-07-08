import MangaRequests

if __name__ == "__main__":
    # title_input = input("Please enter a title: ")
    title_input = "Solo Leveling"
    mangas = MangaRequests.get_manga(title_input)
    chapters = MangaRequests.get_chapters(mangas["data"][0]["id"])
    for chapter in chapters["data"]:
        print(chapter["attributes"]["chapter"])
