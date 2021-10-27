import numpy
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

def load_dataset():
    tokens = list(numpy.load("tokens.npy", allow_pickle=True))
    return tokens[0], tokens[1]

def search_habr(token):
    baseurl = "https://habr.com"
    req = "https://habr.com/en/search/?q=" + token + "&target_type=posts"
    headers = {
        "User-Agent": "Mozilla/5.0 \
            (Macintosh; Intel Mac OS X 10_10_1) \
            AppleWebKit/537.36 (KHTML, like Gecko) \
            Chrome/39.0.2171.95 Safari/537.36"
    }
    body = requests.get(req, headers=headers)
    soup = BeautifulSoup(body.content, "html.parser")
    if soup.find("div", "tm-empty-placeholder") is not None:
        return []
    articles = soup.find_all("article", "tm-articles-list__item")
    if articles in [None, []] :
        return []

    links = []
    for a in range(min(len(articles), 5)):
        header = articles[a].find("a", "tm-article-snippet__title-link")
        if header.get("href", None) is not None:
            links.append(baseurl + header["href"])

    return links

def main():
    tokens, tokens_clear = load_dataset()
    tokens_clear = tokens
    print("[*] debug: TODO clean tokens")
    while True:
        cmd = input("Type in the number of a vacancy [0-"+str(len(tokens)) + "]: ")
        if not cmd.strip().isdigit():
            break
        num = int(cmd.strip())
        print("Found tokens:", tokens[num])
        print("Popular tokens:", tokens_clear[num])
        res = {}
        for tk in tokens_clear[num]:
            res[tk] = search_habr(tk)
        for i in res:
            print(i, res[i], sep=": ")


if __name__ == "__main__":
    main()

