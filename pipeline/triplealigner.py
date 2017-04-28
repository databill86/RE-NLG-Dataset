from pipeline import *
import itertools


class NoSubjectAlign(BasePipeline):
    """
    Following the assumption in NoSUB  [1] and [2] that sentences in one paragraph all share the same subject.
    [1] Augenstein, Isabelle, Diana Maynard, and Fabio Ciravegna. "Distantly supervised web relation extraction for knowledge base population." Semantic Web 7.4 (2016): 335-349.
    [2] WikiReading: A Novel Large-scale Language Understanding Task over Wikipedia Hewlett et al. 2016
    """
    def __init__(self, triples_reference):
        self.annotator_name = "NoSubject-Triple-aligner"

        # pd.read_csv(triples_file, sep="\t", names=["subject", "predicate", "object"]).set_index(['subject', 'object'])

        self.wikidata_triples = triples_reference.d


    def run(self, document):
        """
        :param: input document to align its sentences with triples
        :return:
        """
        for sid, (start, end) in enumerate(document.sentences_boundaries):

            # Getting sentence subject
            # Every sentence has main entity as subject

            # if subject already tagged use it if not use only the URI
            # entities in sentence
            es = [j for j in document.entities if j.boundaries[0] >= start and j.boundaries[1] <= end]
            e_sub = [j for j in es if j.uri == document.uri]
            if len(e_sub) > 0:
                subject = e_sub[0]
            else:
                subject = Entity(document.uri,
                                 boundaries=None,
                                 surfaceform=document.title,
                                 annotator=self.annotator_name)

            for o in es:
                if subject.uri == o.uri:
                    continue

                predicates = self.wikidata_triples["%s\t%s" % (subject.uri, o.uri)]

                for pred in predicates:
                    pred = Entity(pred, boundaries=None, surfaceform=None, annotator=self.annotator_name)

                    triple = Triple(subject=subject,
                                    predicate=pred,
                                    object=o,
                                    sentence_id=sid,
                                    annotator=self.annotator_name
                                    )

                    document.triples.append(triple)

        return document


class SimpleAligner(BasePipeline):
    """
    Take a document with tagged entities and match them with one another.
    Example : If we have three entities Q1, Q2 and Q3, it will try to find a
    property binding Q1 with Q2, Q2 with Q1, Q2 with Q3 etc...
    It won't match Q1 with itself, but if Q1 == Q2, it will try to find a
    property between them
    """
    def __init__(self, triples_reference):
        """
        :param: input document containing the triples (two entities and
        the property that bind them together)
        """
        self.annotator_name = "Simple-Aligner"

        self.wikidata_triples = triples_reference.d

    def run(self, document):
        """
        :param: input document to align its sentences with triples
        :return:
        """
        for sid, (start, end) in enumerate(document.sentences_boundaries):

            es = [j for j in document.entities if j.boundaries[0] >= start and j.boundaries[1] <= end]

            # We use permutations to match every entity with all the others
            for o in itertools.permutations(es, 2):

                if o[0].uri == o[1].uri:
                    continue

                # We grab the predicates
                predicates = self.wikidata_triples["%s\t%s" % (o[0].uri, o[1].uri)]

                # And create the triples
                for pred in predicates:
                    pred = Entity(pred, boundaries=None, surfaceform=None, annotator=self.annotator_name)

                    triple = Triple(subject=o[0],
                                    predicate=pred,
                                    object=o[1],
                                    sentence_id=sid,
                                    annotator=self.annotator_name
                                    )

                    document.triples.append(triple)

        return document


class SPOAligner(BasePipeline):

    def __init__(self, triples_reference):
        self.annotator_name = "SPOAligner"
        # Add here the name of the annotators creating entities with something else than properties
        self.annotator_list = ["Wikidata_Spotlight_Entity_Linker", "Simple_Coreference", "Date_Linker"]

        self.wikidata_triples = triples_reference.d

    def run(self, document):
        for sid, (start, end) in enumerate(document.sentences_boundaries):

            # Entities created by the Entity linkers and the Coreference
            es = [j for j in document.entities if j.boundaries[0] >= start
                                                and j.boundaries[1] <= end
                                                and j.annotator in self.annotator_list]

            # Entities created by the Property Linker
            p = [j for j in document.entities if j.boundaries[0] >= start
                                                and j.boundaries[1] <= end
                                                and j.annotator == 'Wikidata_Property_Linker']

            for o in itertools.permutations(es, 2):

                if o[0].uri == o[1].uri:
                    continue

                predicates = self.wikidata_triples["%s\t%s" % (o[0].uri, o[1].uri)]
                # And create the triples
                for kbpred in predicates:
                    for spred in p:
                        if kbpred == spred.uri:
                            predic = Entity(spred.uri, boundaries=spred.boundaries, surfaceform=spred.surfaceform, annotator=self.annotator_name)

                            triple = Triple(subject=o[0],
                                            predicate=predic,
                                            object=o[1],
                                            sentence_id=sid,
                                            annotator=self.annotator_name
                                            )

                            document.triples.append(triple)

        return document


class NoSubSPOAligner(BasePipeline):

    def __init__(self, triples_reference):
        self.annotator_name = "NosubSPOAligner"
        # Add here the name of the annotators creating entities with something else than properties
        self.annotator_list = ["Wikidata_Spotlight_Entity_Linker", "Simple_Coreference", "Date_Linker"]

        self.wikidata_triples = triples_reference.d

    def run(self, document):
        for sid, (start, end) in enumerate(document.sentences_boundaries):

            # Entities created by the Entity linkers and the Coreference
            es = [j for j in document.entities if j.boundaries[0] >= start
                                                and j.boundaries[1] <= end
                                                and j.annotator in self.annotator_list]

            e_sub = [j for j in es if j.uri == document.uri]


            # Entities created by the Property Linker
            p = [j for j in document.entities if j.boundaries[0] >= start
                                                and j.boundaries[1] <= end
                                                and j.annotator == 'Wikidata_Property_Linker']

            for o in es:
                for subject in e_sub:
                    if subject.uri == o.uri:
                        continue

                    predicates = self.wikidata_triples["%s\t%s" % (subject.uri, o.uri)]
                    # And create the triples
                    for kbpred in predicates:
                        for spred in p:
                            if kbpred == spred.uri:
                                predic = Entity(spred.uri, boundaries=spred.boundaries, surfaceform=spred.surfaceform, annotator=self.annotator_name)

                                triple = Triple(subject=subject,
                                                predicate=predic,
                                                object=o,
                                                sentence_id=sid,
                                                annotator=self.annotator_name
                                                )

                                document.triples.append(triple)

        return document
