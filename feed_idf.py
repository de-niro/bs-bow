import numpy
#import nltk
import string
import re
import sys
import tqdm
from threading import Thread, Lock
#from sklearn.feature_extraction.text import CountVectorizer
from natasha import (
    Segmenter,
    MorphVocab,
    NewsEmbedding,
    NewsMorphTagger,
    NewsSyntaxParser,
    NewsNERTagger,
    PER,
    NamesExtractor,
    Doc,
)

mutex = Lock()

def init_natasha():
    segmenter = Segmenter()
    morph_vocab = MorphVocab()
    
    emb = NewsEmbedding()
    morph_tagger = NewsMorphTagger(emb)
    syntax_parser = NewsSyntaxParser(emb)
    ner_tagger = NewsNERTagger(emb)
    
    names_extractor = NamesExtractor(morph_vocab)
    return {"segmenter": segmenter, "morph_vocab": morph_vocab, "emb": emb, "morph_tagger": morph_tagger,\
            "syntax_parser": syntax_parser, "ner_tagger": ner_tagger, "names_extractor": names_extractor}

def load_dataset():
    words = numpy.load('words.npy', allow_pickle=True)
    return words

def tokenize(words):
    # deprecated
    tokens = []
    for w in words:
        w = w.lower()
        tk = nltk.tokenize.word_tokenize(w)
        tokens.append([t for t in tk if not re.match('[', string.punctuation, ']+', t)])
    return tokens

def vectorize_old(tokens):
    # deprecated
    vc = CountVectorizer()

def find_tokens(nat, text):
    doc = Doc(text)
    doc.segment(nat["segmenter"])
    doc.tag_morph(nat["morph_tagger"])
    for tk in doc.tokens:
        tk.lemmatize(nat["morph_vocab"])
    doc.tag_ner(nat["ner_tagger"])

    res = []
    for sp in doc.spans:
        if sp.type == 'ORG':
            res.append(''.join(list(map(lambda x: x.lemma, sp.tokens))))
    return res

def threaded_find_tokens(nat, text, res, ind):
    tk = find_tokens(nat, text)
    mutex.acquire()
    res[ind] = tk
    mutex.release()

def vectorize(words):
    vectors = {}
    for i in range(len(words)):
        for w in words[i]:
            vectors[w] = vectors.get(w, 0) + 1
    return vectors

def remove_rare(words, vec):
    res = []
    for w in words:
        for tk in tokens:
            if vec[tk] >= 3:
                res.append(tk)

def save_dataset(text):
    numpy.save('tokens.npy', text, allow_pickle=True)

def debug_print():
    print("[*] Initializing Natasha...")
    nat = init_natasha()
    print("[*] Loading dataset...")
    words = load_dataset()
    print("[*] Initializing Doc...")
    doc = Doc(words[int(sys.argv[1])])
    print("[*] Tokenizing words...")
    doc.segment(nat["segmenter"])
    print("[*] Morphing...")
    doc.tag_morph(nat["morph_tagger"])
    print("[*] Lemmatizing...")
    for tk in doc.tokens:
        tk.lemmatize(nat["morph_vocab"])
    print("[*] Tagging...")
    doc.tag_ner(nat["ner_tagger"])
    doc.ner.print()

    res = []
    for sp in doc.spans:
        if sp.type == 'ORG':
            res.append(''.join(list(map(lambda x: x.lemma, sp.tokens))))
                #print(tk.lemma, end=" ")
            #print("; ", end="")
            #print(sp.text, end=", ")
    print(res)
    #tokens = tokenize(words)
    #print(tokens)

def parse_tokens(tokens):
    print("[*] Vectorizing...")
    vec = vectorize(tokens)
    print("[*] Removing rare words...")
    try:
        tokens_clear = remove_rare(tokens, vec)
    except BaseException:
        print("Cannot remove rare tokens, sorry")
        tokens_clear = []
    print("[*] Saving dataset...")
    save_dataset([tokens, tokens_clear])

def threaded_launch():
    threads_num = 4
    print("[*] Initializing Natashas...")
    nats = []
    for _ in range(threads_num):
        nats.append(init_natasha())
    print("[*] Loading dataset...")
    words = load_dataset()
    tokens = []
    for text in tqdm.tqdm(range(0, len(words), threads_num), desc="Running NLP...", ncols=100):
        thr = threads_num
        if len(words) - text < 4:
            thr = len(words) % threads_num

        threads = [None]*thr
        results = [None]*thr
        for i in range(thr):
            threads[i] = Thread(target=threaded_find_tokens, args=(nats[i], words[text + i], results, i))
            threads[i].start()

        for i in range(thr):
            threads[i].join()

        for r in results:
            tokens.append(r)
    return tokens

def launch():
    print("[*] Initializing Natasha...")
    nat = init_natasha()
    print("[*] Loading dataset...")
    words = load_dataset()
    tokens = []
    for text in tqdm.tqdm(words, desc="Running NLP...", ncols=100):
        tokens.append(find_tokens(nat, text))
    return tokens

def main():
    tokens = threaded_launch()
    parse_tokens(tokens)

if __name__ == "__main__":
    main()
    #debug_print()

