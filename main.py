import MangaRequests
from pyfiglet import Figlet

f = Figlet(font='slant')


def main_menu():
    print(f.renderText('MangaDex Tool'))
    title_input = input("Please enter a title: ")
    mangas = MangaRequests.get_mangas(title_input)
    i = 1
    print("The following results where found, please choose one:")
    for manga in mangas:
        print(f"{i}: {manga['attributes']['title']['en']}")
        i += 1

    choice = int(input("Please enter a number: "))
    chapters = MangaRequests.get_chapters(mangas[choice - 1]["id"])

    print("Downloading images... (This may take a while)")
    MangaRequests.get_all_images(chapters, mangas[choice - 1]['attributes']['title']['en'])
    # for index, row in chapters.iterrows():
    #   MangaRequests.get_images(row["id"], mangas[choice - 1]['attributes']['title']['en'], row["chapter"])
    # MangaRequests.create_pdf(mangas[choice - 1]['attributes']['title']['en'], row["chapter"])

    if manga:
        MangaRequests.pdf_combine(mangas[choice - 1]['attributes']['title']['en'])
    print("Done!")


if __name__ == "__main__":
    main_menu()
