import os
import datetime
import logging
from math import fabs
from time import time
import re
import sys

from sklearn.feature_extraction.text import TfidfVectorizer
from unidecode import unidecode

try:
    import nmslib
    have_nmslib = True
except ImportError:
    have_nmslib = False

logger = logging.getLogger(__name__)

def ngrams(string, n=3):
    """ Take a lookup string (noise removed, lower case, etc) and turn into a list of trigrams """

    string = ' ' + string + ' '  # pad names for ngrams...
    ngrams = zip(*[string[i:] for i in range(n)])
    return [''.join(ngram) for ngram in ngrams]


class FuzzyIndex:
    '''
       Create a fuzzy index using a Term Frequency, Inverse Document Frequency (tf-idf)
       algorithm. Currently the libraries that implement this cannot be serialized to disk,
       so this is an in memory operation. Fortunately for our amounts of data, it should
       be quick to rebuild this index.
    '''

    def __init__(self):
        global have_nmslib

        self.have_nmslib = have_nmslib
        self.vectorizer = None
        self.index = None

    def encode_string(self, text):
        if text is None:
            return None
        return unidecode(re.sub(" +", "", re.sub(r'[^\w ]+', '', text)).strip().lower())

    def build(self, artist_recording_data):
        """
            Builds a new index and saves it to disk and keeps it in ram as well.
        """

        if not self.have_nmslib:
            return

        self.lookup_strings = []
        lookup_ids = []
        for artist_name, recording_name, lookup_id in artist_recording_data:
            if artist_name is None or recording_name is None:
                continue
            self.lookup_strings.append(self.encode_string(artist_name) + self.encode_string(recording_name))
            lookup_ids.append(lookup_id)

        self.vectorizer = TfidfVectorizer(min_df=1, analyzer=ngrams)
        lookup_matrix = self.vectorizer.fit_transform(self.lookup_strings)

        self.index = nmslib.init(method='simple_invindx', space='negdotprod_sparse_fast', data_type=nmslib.DataType.SPARSE_VECTOR)
        self.index.addDataPointBatch(lookup_matrix, lookup_ids)
        self.index.createIndex()

    def search(self, query_data):
        """
            Return IDs for the matches in a list. Returns a list of dicts with keys of lookup_string, confidence and recording_id.
        """
        if not self.have_nmslib:
            logger.warn("nmslib not installed and trying fuzzy search, but nothing will match. Install nmslib!")
            return []

        query_strings = []
        for data in query_data:
            if data["artist_name"] is None or data["recording_name"] is None:
                continue

            query_strings.append(self.encode_string(data["artist_name"]) + self.encode_string(data["recording_name"]))

        query_matrix = self.vectorizer.transform(query_strings)
        results = self.index.knnQueryBatch(query_matrix, k=1, num_threads=1)

        output = []
        for i, result in enumerate(results):
            if len(result[0]):
                output.append({"confidence": fabs(result[1][0]),
                               "recording_id": result[0][0]})
            else:
                output.append({"confidence": 0.0, "recording_id": 0})

        return output
