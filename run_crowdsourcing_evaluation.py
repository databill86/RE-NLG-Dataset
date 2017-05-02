# read files
import pandas as pd
import random

random.seed(4)

DOC_NUM = 1000
titles = pd.read_csv('./crowdsourcing/GR7bQ7Ra.tsv', sep="\t")["title"].values
titles = [i.replace("_", " ") for i in titles]

titles = random.sample(titles, 500000)

from pipeline.entitylinker import *
from pipeline.triplealigner import *
from pipeline.datareader import DBpediaAbstractsDataReader
from pipeline.writer import JsonWriter
from pipeline.coreference import *
from utils.triplereader import *

start_doc = 0   # start reading from document number #

# Reading the DBpedia Abstracts Dataset
reader = DBpediaAbstractsDataReader('./datasets/wikipedia-abstracts/csv/dbpedia-abstracts.csv', db_wd_mapping='./datasets/wikidata/dbpedia-wikidata-sameas-dict.csv', skip=start_doc)

# Loading the WikidataSpotlightEntityLinker ... DBpedia Spotlight with mapping DBpedia URIs to Wikidata
link = WikidataSpotlightEntityLinker('./datasets/wikidata/dbpedia-wikidata-sameas-dict.csv', support=10, confidence=0.4)


coref = SimpleCoreference()
trip_read = TripleReader('./datasets/wikidata/wikidata-triples.csv')
Salign = SimpleAligner(trip_read)
prop = WikidataPropertyLinker('./datasets/wikidata/wikidata-properties.csv')
date = DateLinker()
SPOalign = SPOAligner(trip_read)
NSalign = NoSubjectAlign(trip_read)
writer = JsonWriter('./crowdsourcing/out', "re-nlg-eval", startfile=start_doc, filesize=DOC_NUM)
Nospoalign = NoSubSPOAligner(trip_read)

for d in reader.read_documents():

    if d.title not in titles:
        continue

    try:
        d = link.run(d)
        d = date.run(d)
        d = NSalign.run(d)
        d = coref.run(d)
        d = Salign.run(d)

        d = prop.run(d)
        d = Nospoalign.run(d)
        d = SPOalign.run(d)

        writer.run(d)
        print "Document Title: %s \t Number of Annotated Entities %s \t Number of Annotated Triples %s" % (d.title, len(d.entities), len(d.triples))

    except Exception as e:

        print "error Processing document %s" % d.title







