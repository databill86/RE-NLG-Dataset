# -*- coding: utf-8 -*-

from pipeline import *
import spotlight
import csv
import re
import json
import os
from sutime import SUTime


# class DBSpotlightEntityLinker(BasePipeline):
#
#     def __init__(self, spotlight_url='http://localhost:2222/rest/annotate', confidence=0.2, support=1):
#         """
#         :param spotlight_url: url of the dbpedia spotlight service
#         :param confidence: min confidence
#         :param support:  min supporting document
#         """
#         self.annotator_name = 'DBpedia_spotlight'
#         self.spotlight_url = spotlight_url
#         self.confidence = confidence
#         self.support = support
#
#     def run(self, document):
#         """
#         :param document: Document object
#         :return: Document after being annotated
#         """
#
#         #document.entities = []
#
#         for sid, (start, end) in enumerate(document.sentences_boundaries):
#
#             try:
#                 annotations = spotlight.annotate(self.spotlight_url,
#                                                  document.text[start:end],
#                                                  self.confidence,
#                                                  self.support)
#
#             except Exception as e:
#                 annotations = []
#
#             for ann in annotations:
#
#                 e_start = document.sentences_boundaries[sid][0] + ann['offset']
#
#                 if type(ann['surfaceForm']) not in [str, unicode]:
#                     ann['surfaceForm'] = str(ann['surfaceForm'])
#
#                 e_end = e_start + len(ann['surfaceForm'])
#
#                 entity = Entity(ann['URI'],
#                                 boundaries=(e_start, e_end),
#                                 surfaceform=ann['surfaceForm'],
#                                 annotator=self.annotator_name)
#
#                 document.entities.append(entity)
#
#         return document
#
#
# class DBSpotlightEntityAndTypeLinker(BasePipeline):
#     """
#     Since DBpedia spotlight only tag resources not types
#     for example the sentence :
#     Berlin was the capital of the Kingdom of Prussia
#     will get you the <http://dbpedia.org/resource/Capital_city> not the <http://dbpedia.org/ontology/Capital>
#     so we can't map it to the triple
#     <http://dbpedia.org/resource/Berlin> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/Capital> .
#     This Entity linker tries to alleviate that by searching is the resource matches a DBpedia ontology class
#     """
#
#     def __init__(self, dbo_file, dict_file, spotlight_url='http://localhost:2222/rest/annotate', confidence=0.2, support=1):
#         """
#         :param dbo_file:  file path containing all valid dbpedia classes, default ./datasets/dbpedia/dbpedia-classes.txt
#         :param spotlight_url: url of the dbpedia spotlight service
#         :param confidence: min confidence
#         :param support:  min supporting document
#         """
#         self.annotator_name = 'DBpedia-spotlight-Entity-Type-Linker'
#         self.spotlight_url = spotlight_url
#         self.confidence = confidence
#         self.support = support
#         with open(dbo_file) as f:
#             self.dbo_classes = set([i.strip() for i in f.readlines()])
#
#     def run(self, document):
#         """
#         :param document: Document object
#         :return: Document after being annotated
#         """
#
#         #document.entities = []
#
#         for sid, (start, end) in enumerate(document.sentences_boundaries):
#
#             try:
#                 annotations = spotlight.annotate(self.spotlight_url,
#                                                  document.text[start:end],
#                                                  self.confidence,
#                                                  self.support)
#
#             except Exception as e:
#                 annotations = []
#
#             for ann in annotations:
#
#                 e_start = document.sentences_boundaries[sid][0] + ann['offset']
#
#                 if type(ann['surfaceForm']) not in [str, unicode]:
#                     ann['surfaceForm'] = str(ann['surfaceForm'])
#
#                 e_end = e_start + len(ann['surfaceForm'])
#
#                 # give priority to Tag DBpedia classes if they are tagged.
#                 tmp = ann['URI'].replace("resource", "ontology")
#                 if tmp in self.dbo_classes:
#                     ann['URI'] = tmp
#
#                 entity = Entity(ann['URI'],
#                                 boundaries=(e_start, e_end),
#                                 surfaceform=ann['surfaceForm'],
#                                 annotator=self.annotator_name)
#
#                 document.entities.append(entity)
#
#         return document
#

class WikidataSpotlightEntityLinker(BasePipeline):

    def __init__(self, db_wd_mapping, spotlight_url='http://localhost:2222/rest/annotate', confidence=0.2, support=1):
        """
        :param db_wd_mapping: csv file name containing mappings between DBpedia URIS and Wikdiata URIS
        :param spotlight_url: url of the dbpedia spotlight service
        :param confidence: min confidence
        :param support:  min supporting document
        """
        self.annotator_name = 'Wikidata_Spotlight_Entity_Linker'
        self.spotlight_url = spotlight_url
        self.confidence = confidence
        self.support = support

        self.mappings = {}
        with open(db_wd_mapping) as f:
            for l in f.readlines():
                tmp = l.split("\t")
                self.mappings[tmp[0].strip()] = tmp[1].strip()

    def run(self, document):
        """
        :param document: Document object
        :return: Document after being annotated
        """

        #document.entities = []

        for sid, (start, end) in enumerate(document.sentences_boundaries):

            try:
                annotations = spotlight.annotate(self.spotlight_url,
                                                 document.text[start:end],
                                                 self.confidence,
                                                 self.support)

            except Exception as e:
                annotations = []

            for ann in annotations:

                e_start = document.sentences_boundaries[sid][0] + ann['offset']

                if type(ann['surfaceForm']) not in [str, unicode]:
                    ann['surfaceForm'] = str(ann['surfaceForm'])

                e_end = e_start + len(ann['surfaceForm'])

                # change DBpedia URI to Wikidata URI
                if ann['URI'] in self.mappings:
                    ann['URI'] = self.mappings[ann['URI']]
                else:
                    continue

                entity = Entity(ann['URI'],
                                boundaries=(e_start, e_end),
                                surfaceform=ann['surfaceForm'],
                                annotator=self.annotator_name)

                document.entities.append(entity)

        return document



class WikidataSpotlightEntityLinkerWithCustomSupportAndFilter(BasePipeline):

    def __init__(self, db_wd_mapping, spotlight_url='http://localhost:2222/rest/annotate', confidence=0.35, support_list=(20, 13, 6, -1)):
        """
        a class for annotation using DBpedia spotlight and then mapping the output URIs to wikidata.
        The class takes a support as a list that checks if the returned annotation has the doc.uri inside
        if not it tries using the 2nd item in the support list .
        After scanning all support list if it doesn't find the main Item in the returned entities
        it returns None.  In the run file you should check d is not None to skip those documents

        :param db_wd_mapping: csv file name containing mappings between DBpedia URIS and Wikdiata URIS
        :param spotlight_url: url of the dbpedia spotlight service
        :param confidence: min confidence
        :param support:  list of support values, support value is a the min supporting document parameter to be passed to DBpedia spotlight
        """
        self.annotator_name = 'Wikidata_Spotlight_Entity_Linker'
        self.spotlight_url = spotlight_url
        self.confidence = confidence
        self.support_list = support_list

        self.mappings = {}
        with open(db_wd_mapping) as f:
            for l in f.readlines():
                tmp = l.split("\t")
                self.mappings[tmp[0].strip()] = tmp[1].strip()

    def run(self, document):
        """
        :param document: Document object
        :return: Document after being annotated
        """

        for support in self.support_list:

            entities_list = []
            main_entity_annotated = False


            for sid, (start, end) in enumerate(document.sentences_boundaries):

                try:
                    annotations = spotlight.annotate(self.spotlight_url,
                                                     document.text[start:end],
                                                     self.confidence,
                                                     support)

                except Exception as e:
                    annotations = []

                for ann in annotations:

                    e_start = document.sentences_boundaries[sid][0] + ann['offset']

                    if type(ann['surfaceForm']) not in [str, unicode]:
                        ann['surfaceForm'] = str(ann['surfaceForm'])

                    e_end = e_start + len(ann['surfaceForm'])

                    # change DBpedia URI to Wikidata URI
                    if ann['URI'] in self.mappings:
                        ann['URI'] = self.mappings[ann['URI']]
                    else:
                        continue


                    if ann['URI'] == document.uri:
                        main_entity_annotated = True

                    entity = Entity(ann['URI'],
                                    boundaries=(e_start, e_end),
                                    surfaceform=ann['surfaceForm'],
                                    annotator=self.annotator_name)


                    entities_list.append(entity)
                    # document.entities.append(entity)

            if main_entity_annotated:
                for e in entities_list:
                    document.entities.append(e)

                return document

        # if arrives here then main entity isn't found and no entity is annotated.
        return document


class WikidataPropertyLinker(BasePipeline):

    def __init__(self, wd_prop_mapping):
        self.annotator_name = 'Wikidata_Property_Linker'

        self.mappings = {}
        with open(wd_prop_mapping) as f:
            for l in csv.reader(f, delimiter='\t'):
                self.mappings[l[2]] = l[0]

    def run(self, document):
        dict_keys = self.mappings.keys()
        stop_words = ["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself",
                      "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its",
                      "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this",
                      "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has",
                      "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or",
                      "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between",
                      "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down",
                      "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there",
                      "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other",
                      "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t",
                      "can", "will", "just", "don", "should", "now"]

        for prop in dict_keys:
            for m in re.finditer(r"\b" + re.escape(prop) + r"\b", document.text):
                (start, end) = m.start(), m.end()
                if document.text[start:end] not in stop_words:
                    entity = Entity(self.mappings[document.text[start:end]],
                                    boundaries=(start, end),
                                    surfaceform=document.text[start:end],
                                    annotator=self.annotator_name)

                    document.entities.append(entity)

        return document

class KeywordMatchingEntityLinker(BasePipeline):

    def __init__(self, trip_read_items, label_read):
        self.annotator_name = 'Keyword_Matching_Entity_Linker'
        self.trip_read_items = trip_read_items
        self.label_read = label_read

    def run(self, document):
        # iterate over URIs
        for uri in self.trip_read_items.get(document.docid):
            # get array of labels for URI
            labels = self.label_read.get(uri)
            for x in labels:
                # look for label in the text
                delims = re.escape(u"\".؟()[]?,' ")
                for m in re.finditer(r"(^|[%s])(%s)([%s]|$)"%(delims, x.lower(), delims), document.text.lower()):

                    (start, end) = m.span(2)

                    # create entitity if match is found
                    entity = Entity(uri,
                                    boundaries=(start, end),
                                    surfaceform=document.text[start:end],
                                    annotator=self.annotator_name)
                    # add entity to document
                    document.entities.append(entity)

        return document

class DateLinker(BasePipeline):

    def __init__(self, resource_folder=None):
        self.annotator_name = 'Date_Linker'
        if resource_folder is None:
            self.resource_folder = os.path.join(os.path.dirname(__file__), '../resources/sutime/')
        self.sutime = SUTime(jars=self.resource_folder)

    def run(self, document):

        dates = self.sutime.parse(document.text)

        pattern = re.compile(r"^-*\d*-*\d*-*\d*-*$")

        for date in dates:
            if date["type"] == "DATE" and pattern.match(date["value"]):
                val = date["value"]
                if val[0] == '-':
                    if len(val[1:]) == 4:
                        stdform = val + '-00-00T00:00:00Z^^http://www.w3.org/2001/XMLSchema#dateTime'
                    elif len(val[1:]) == 7:
                        stdform = val + '-00T00:00:00Z^^http://www.w3.org/2001/XMLSchema#dateTime'
                    elif len(val[1:]) == 10:
                        stdform = val + 'T00:00:00Z^^http://www.w3.org/2001/XMLSchema#dateTime'
                    else:
                        stdform = val + '^^<http://www.w3.org/2001/XMLSchema#dateTime>'

                else:
                    if len(val) == 4:
                        stdform = val + '-00-00T00:00:00Z^^http://www.w3.org/2001/XMLSchema#dateTime'
                    elif len(val) == 7:
                        stdform = val + '-00T00:00:00Z^^http://www.w3.org/2001/XMLSchema#dateTime'
                    elif len(val) == 10:
                        stdform = val + 'T00:00:00Z^^http://www.w3.org/2001/XMLSchema#dateTime'
                    else:
                        stdform = val + '^^<http://www.w3.org/2001/XMLSchema#dateTime>'

                start = date["start"]
                end = date["end"]

                entity = Entity(uri=stdform,
                                boundaries=(start, end),
                                surfaceform=document.text[start:end],
                                annotator=self.annotator_name)

                document.entities.append(entity)

        return document
