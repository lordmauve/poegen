import re
import random
from collections import defaultdict, Counter


PRONUNCIATION_DICT = 'cmudict.0.7a'
POEM_LINES = 'lines.txt'
PHONEME_TABLE = 'cmudict.0.7a.phones'


def stripped_lines(fname):
    """Iterate over the stripped, non-blank lines of fname."""
    for l in open(fname):
        l = l.strip()
        if l:
            yield l


def pronunciation_dict():
    """Iterate over the pronunciation dictionary as (word, phonemes list)."""
    for l in stripped_lines(PRONUNCIATION_DICT):
        toks = l.strip().split()
        word = toks[0].rstrip('()')
        phonemes = toks[1:]
        yield word, phonemes


def load_rhyme_dict():
    phones = CMUPhones()
    word_table = {}
    for word, phonemes in pronunciation_dict():
        curphon = []
        for p in reversed(phonemes):
            p = re.sub(r'\d', '', p)  # Strip phomeme stresses
            curphon.append(p)
            if phones.is_vowel(p) and len(curphon) > 1:
                break
        word_table[word] = tuple(curphon)
    return word_table


class CMUPhones(object):
    """A table of phoneme types."""
    def __init__(self):
        self.read_phones()

    def read_phones(self):
        self.phones = dict(l.split() for l in stripped_lines(PHONEME_TABLE))

    def is_vowel(self, c):
        return self.phones.get(c) == 'vowel'


def last_word(line):
    """Return the last word in a line (stripping punctuation).

    Raise ValueError if the last word cannot be identified.

    """
    mo = re.search(r"([\w']+)\W*$", line)
    if mo:
        w = mo.group(1)
        w = re.sub(r"'d$", 'ed', w)  # expand old english contraction of -ed
        return w.upper()
    raise ValueError("No word in line.")


class RhymingLines(object):
    def __init__(self):
        """Collect poem lines into groups of lines that all rhyme."""

        # A dict of dicts {rhyme key: {last word: list of lines}}
        self.rhyme_groups = defaultdict(lambda: defaultdict(list))

        rhymedict = load_rhyme_dict()
        for l in stripped_lines(POEM_LINES):
            w = last_word(l)
            try:
                rhyme = rhymedict[w]
            except (KeyError, ValueError):
                continue

            self.rhyme_groups[rhyme][w].append(l)

    def pick_lines(self, n=2):
        """Pick and remove n unique lines."""

        # Pick a rhyme group that contains at least n unique last words
        groups = [k for k, v in self.rhyme_groups.iteritems() if len(v) >= n]
        gk = random.choice(groups)

        # Pick n groups of lines with common last words
        line_groups = self.rhyme_groups[gk].values()
        del self.rhyme_groups[gk]
        lines_by_word = random.sample(line_groups, n)

        # Pick one line from each group
        return [random.choice(ls) for ls in lines_by_word]


def terminate_poem(poem):
    """Given a list of poem lines, fix the punctuation of the last line.

    Removes any non-word characters and substitutes a random sentence
    terminator - ., ! or ?.

    """
    last = re.sub(r'\W*$', '', poem[-1])
    punc = random.choice('!.?')
    return poem[:-1] + [last + punc]


def build_poem(rhyme_scheme, rhymes):
    """Build a poem given a rhymne scheme, eg aabbcaa.

    Spaces are translated to paragraph breaks.

    """
    groups = Counter(rhyme_scheme.replace(' ', ''))

    lines = {}

    # Choose the lines to use
    for k, n in groups.iteritems():
        lines[k] = rhymes.pick_lines(n)

    # Build the poem
    poem = []
    for k in rhyme_scheme:
        if k == ' ':
            if poem:
                poem = terminate_poem(poem) + ['']
        else:
            poem.append(lines[k].pop())
    return terminate_poem(poem)


if __name__ == '__main__':
    import sys

    rhyme_scheme = ' '.join(sys.argv[1:]) or 'aabba'

    rhymes = RhymingLines()
    poem = build_poem(rhyme_scheme, rhymes)
    print '\n'.join(poem)
