import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import json
import numpy
from threading import Thread, Lock

mutex = Lock()

def fetch_rates():
    # We need to fetch current USD-RUB rate
    pr = requests.get("https://www.cbr-xml-daily.ru/daily_json.js")
    p = json.loads(pr.content)
    usd = p["Valute"]["USD"]["Value"]
    eur = p["Valute"]["EUR"]["Value"]
    uah = p["Valute"]["UAH"]["Value"]
    kzt = p["Valute"]["KZT"]["Value"]
    return {"usd": usd, "eur": eur, "uah": uah, "kzt": kzt}

def parse_title(v, headers, base_url, res, ind):
    lnk = v.find("a", "vacancy-card__title-link")["href"]
    if lnk == None:
        return None
    vac_b = requests.get(base_url + lnk, headers=headers)
    if not vac_b.ok:
        return None

    vs = BeautifulSoup(vac_b.content, "html.parser")

    v_body_wr = vs.find("div", "job_show_description__vacancy_description")
    if v_body_wr is None:
        print("Cannot find vacancy body")
        return None

    v_body = v_body_wr.find("div", "style-ugc").get_text()
    
    mutex.acquire()
    res[ind] = v_body
    mutex.release()
    #return v_body

def save_dataset(text):
    numpy.save('words.npy', text, allow_pickle=True)

def fetch_vacancies(rates):
    divisions=["backend", "frontend", "apps", "software", "testing", "administration", "design", "management",\
           "marketing", "analytics", "sale", "content", "support", "hr", "office", "telecom", "other", "security"]
    base_url = "https://career.habr.com/vacancies?divisions[]="
    prices_avg = {}
    prices_max = {}
    text = []
    headers = {
        "User-Agent": "Mozilla/5.0 \
           (Macintosh; Intel Mac OS X 10_10_1) \
           AppleWebKit/537.36 (KHTML, like Gecko) \
           Chrome/39.0.2171.95 Safari/537.36"
    }

    for i in tqdm(divisions, desc="parsing..."):
        page = 0
        #prices_avg[i] = []
        #prices[i] = []
        while True:
            if page == 0:
                req = requests.get(base_url + i + "&type=all", headers=headers)
            else:
                req = requests.get(base_url + i + "&type=all&page=" + str(page),\
                                  headers=headers)
            if not req.ok:
                break
            sp = BeautifulSoup(req.content, "html.parser")
            vc = sp.find_all("div", "vacancy-card")
            if vc == []:
                break
            threads = [None] * len(vc)
            results = [None] * len(vc)
            for j in range(len(vc)):
                threads[j] = Thread(target=parse_title, args=(vc[j], headers, "https://career.habr.com", results, j))
                threads[j].start()

            for j in range(len(threads)):
                threads[j].join()
            
            for r in results:
                #v_text = parse_title(v, headers, "https://career.habr.com")
                if r is not None:
                    text.append(r)
            page += 1
    return text

def load_file():
    a = numpy.load("words.npy", allow_pickle=True)
    print(a)

def main():
    rates = fetch_rates()

    text = fetch_vacancies(rates)

    save_dataset(text)
    

if __name__ == "__main__":
    main()



