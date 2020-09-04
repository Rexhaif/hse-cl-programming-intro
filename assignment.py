import pandas as pd
import argparse as ap

import re
import json
import string
import requests

from pathlib import Path
from collections import Counter
from pymystem3 import Mystem
from bs4 import BeautifulSoup


def remove_punctuations(sen: str) -> str:
    punctuation = re.escape(string.punctuation) + "\ufeff" + "«–»"  # some specific punctuation
    return ' '.join(re.findall(f'[^{punctuation}\s]+', sen))


def check_o(lemma: str, o_count: int = 2) -> bool:
    if "о" in lemma:
        return Counter(lemma)["о"] == o_count
    else:
        return False


def download_and_open(file_name: str, source_url: str, encoding: str = 'koi8-r'):
    r = requests.get(source_url, stream=True)
    file = Path(file_name)

    if not file.exists():  # caching
        with open(file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=16 * 1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
            f.close()

    with open(file, 'r', encoding=encoding) as f:
        return f.read()


if __name__ == '__main__':
    parser = ap.ArgumentParser(prog='assignment.py')
    parser.add_argument("-i", "--input", type=str, help="input path")
    parser.add_argument("-f", "--freq-vocab", type=str, help="frequency vocab path")
    parser.add_argument("-o", "--double-o-lemmas", type=str, help="double 'o' lemmas file path")
    parser.add_argument("-v", "--vocab-file", type=str, help="lirika.txt vocab file")

    args: ap.Namespace = parser.parse_args()
    # -- Part 1 --
    with open(args.input, 'r', encoding='utf-8') as f:
        text = " ".join(map(remove_punctuations, map(lambda x: x.lower(), f.readlines())))

    words = text.split()
    freq_vocab = Counter(words)
    dataframe = pd.DataFrame(freq_vocab.most_common(), columns=['Word', "#Occurencies"])
    dataframe.to_csv(args.freq_vocab, index=False, encoding='utf-8')
    print("Done creating frequency vocab for part 1")
    # -- Part 2 --
    mystem = Mystem()
    double_o_lemmas = list(
        filter(
            check_o,
            map(
                lambda x: mystem.lemmatize(x)[0],
                words
            )
        )
    )
    with open(args.double_o_lemmas, "w", encoding="utf-8") as f:
        f.write(" ".join(double_o_lemmas))
    print("Done creating lemma list for part 2")

    lirika_text = download_and_open("lirika.txt", "http://lib.ru/POEZIQ/PESSOA/lirika.txt")
    bs = BeautifulSoup(lirika_text, features="html.parser")
    lirika_text = bs.get_text()

    # removing table of contents
    lirika_text = lirika_text.split("\n")
    lirika_text = lirika_text[:lirika_text.index("СОДЕРЖАНИЕ") - 4]
    # removing weird === [ ] ==== lines
    lirika_text = re.sub(r'\s*([-=]*)\s\[(.*?)\]\s(=*)\s*', '', "\n".join(lirika_text))
    # removing punctuation
    lirika_text = remove_punctuations(lirika_text).lower()
    vocab = {word: i for i, word in enumerate(set(lirika_text.split()))}
    with open(args.vocab_file, 'w', encoding="utf-8") as f:
        json.dump(vocab, f, indent=2, ensure_ascii=False)
    print("Done creating vocab for part 2")
