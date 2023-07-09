import MangaRequests

if __name__ == "__main__":
    # title_input = input("Please enter a title: ")
    # title_input = "Solo Leveling"
    # mangas = MangaRequests.get_manga(title_input)
    chapter = MangaRequests.get_chapters("32d76d19-8a05-4db0-9fc2-e0b0648fe9d0")
    # chapters = MangaRequests.get_chapters(mangas["data"][0]["id"])
    # for chapter in chapters["data"]:
    #   print(chapter["attributes"]["chapter"])
