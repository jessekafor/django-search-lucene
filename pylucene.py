# -*- coding: utf-8 -*-
"""
 Copyright 2008 Spike^ekipS <spikeekips@gmail.com>

    This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

import sys, random, datetime

from django.conf import settings

import constant

lucene = constant.import_lucene()

######################################################################
# Classes
class __LUCENE__ (object) :

    def __init__ (self, storage_path=None, storage_type=None) :
        # set storage path and type.
        if not storage_path :
            storage_path = settings.SEARCH_STORAGE_PATH

        if not storage_type :
            storage_type = settings.SEARCH_STORAGE_TYPE

        self.storage = None
        self.storage_path = storage_path
        self.storage_type = storage_type

    def is_locked (self) :
        return lucene.IndexReader.isLocked(settings.SEARCH_STORAGE_TYPE)

    def open_storage (self) :
        if self.storage_type == "ram" :
            self.storage = lucene.RAMDirectory()
        else :
            self.storage = lucene.FSDirectory.getDirectory(
                self.storage_path,
            )

    def close_storage (self) :
        if self.storage :
            self.storage.close()
            self.storage = None

class __LUCENE_WRITER__ (__LUCENE__) :
    def __init__ (
                self,
                storage_path=None,
                storage_type=None,
                analyzer=None,
                field_analyzers=dict()
            ) :
        super(__LUCENE_WRITER__, self).__init__(
            storage_path=storage_path, storage_type=storage_type
        )
        self.analyzer = analyzer
        self.field_analyzers = field_analyzers
        self.writer = None

    def get_analyzer (self) :
        if self.analyzer :
            default_analyzer = self.analyzer
        else :
            default_analyzer = lucene.WhitespaceAnalyzer()

        analyzer = lucene.PerFieldAnalyzerWrapper(default_analyzer)
        for field_name, a in self.field_analyzers.items() :
            analyzer.addAnalyzer(field_name, a)

        return analyzer

    def open (self, create=False, field_analyzers=dict()) :
        self.open_storage()
        analyzer = self.get_analyzer()
        for field_name, a in field_analyzers.items() :
            analyzer.addAnalyzer(field_name, a)

        self.writer = lucene.IndexWriter(
            self.storage,
            analyzer,
            isinstance(self.storage, lucene.RAMDirectory) and True or create,
        )

        return self

    def close (self) :
        if self.writer :
            self.writer.close()
            self.writer = None

        self.close_storage()

        return self

class Indexer (__LUCENE_WRITER__) :
    def clean (self) :
        self.open(create=True)
        self.close()

        return self

    def optimize (self) :
        self.open()
        self.writer.optimize(True)
        self.close()

        return self

class IndexWriter (__LUCENE_WRITER__) :
    def unindex_by_term (self, term) :
        self.open()
        self.writer.deleteDocuments(term)

        r = self.writer.hasDeletions()
        self.close()

        return r

    unindex = unindex_by_term

    def index (self, doc, uid=None) :
        # check whether index db is locked.
        self.open()
        if uid :
            self.writer.updateDocument(
                Term.new(constant.FIELD_NAME_UID, uid, ),
                doc,
            )
        else :
            self.writer.addDocument(doc, )

        self.writer.flush()
        self.writer.optimize()

        self.close()
        return self

class Searcher (__LUCENE__) :
    def __init__ (self, storage_path=None, storage_type=None) :
        super(Searcher, self).__init__(
            storage_path=storage_path, storage_type=storage_type
        )
        self.searcher = None

    def open (self) :
        self.open_storage()
        self.searcher = lucene.IndexSearcher(self.storage)

        return self

    def close (self) :
        if self.searcher :
            self.searcher.close()
            self.searcher = None

        self.close_storage()

        return self

    def get_document_by_uid (self, uid) :
        query = BooleanQuery()
        query.add(
            lucene.TermQuery(
                Term.new(constant.FIELD_NAME_UID, uid)
            ),
            constant.QUERY_BOOLEANS.get("AND"),
        )

        try :
            return list(self.search(query))[0]
        except :
            return None

    def get_hits (self, query, sort=lucene.Sort.RELEVANCE, slice=None) :
        """<searcher> and <storage> must be closed after getting documents."""

        _open_searcher = False
        if self.searcher is None :
            _open_searcher = True
            self.open()

        if sort == constant.SORT_RANDOM :
            sort = lucene.Sort.RELEVANCE

        try :
            hits = self.searcher.search(query, sort)
        except SystemError :
            hits = self.searcher.search(query, lucene.Sort.RELEVANCE)

        return hits

    def search (self, query, sort=lucene.Sort.RELEVANCE, slice=None) :
        self.open()

        hits = self.get_hits(query, sort=sort, slice=slice, )
        if settings.DEBUG :
            print
            print "\t=================================================="
            print "\tQuery: %s" % [unicode(query), ]
            print "\tSort : %s" % sort
            print "\tSlice: %s" % slice
            print "\tHits : %d" % (hits.length(), )
            print

        if sort == constant.SORT_RANDOM : # random sort
            l = range(hits.length())
            random.shuffle(l)

            amount = None
            if slice and slice.stop and slice.start :
                amount = int((slice.stop - slice.start) / (slice.step and slice.step or 1))

            hits_iterator = hits.iterator()
            r = dict()
            n = 0
            while True :
                if (amount and n > amount) or not hits_iterator.hasNext() :
                    self.close()
                    break

                if n in l :
                    hit = lucene.Hit.cast_(hits_iterator.next())
                    r[n] = (hit, hit.getDocument(), self.searcher.explain(query, hit.getId(), ))

                n += 1

            for i in l :
                yield r[i]
        else :
            n = 0
            hits_iterator = hits.iterator()
            while True :
                if not hits_iterator.hasNext() :
                    self.close()
                    break

                hit = hits_iterator.next()
                if slice and slice.start and n < slice.start :
                    n += 1
                    continue

                if slice and slice.stop and n >= slice.stop :
                    self.close()
                    break

                hit = lucene.Hit.cast_(hit)
                try:
                    yield (hit, hit.getDocument(), self.searcher.explain(query, hit.getId(), ))
                except lucene.JavaError :
                    self.close()
                    break

                n += 1

class Reader (__LUCENE__) :
    def __init__ (self, storage_path=None, storage_type=None) :
        super(Reader, self).__init__(
            storage_path=storage_path, storage_type=storage_type
        )
        self.reader = None
        self.num_docs_cache = None

    def open (self) :
        self.open_storage()
        self.reader = lucene.IndexReader.open(self.storage)

        return self

    def close (self) :
        if self.reader :
            self.reader.close()
            self.reader = None

        self.close_storage()

        return self

    def num_docs (self) :
        try :
            __last = self.last_modified_time()
            if self.num_docs_cache and self.__last_modified_time and __last >= self.__last_modified_time :
                return self.num_docs_cache
            else :
                self.open()
                self.__last_modified_time = __last

                self.num_docs_cache = self.reader.numDocs()
                self.close()

                return self.num_docs_cache
        except lucene.JavaError, e :
            raise constant.StorageException, e

    def get_version (self) :
        self.open_storage()
        v = lucene.IndexReader.getCurrentVersion(self.storage)
        self.close_storage()
        return v

    def is_optimized (self) :
        self.open()
        b = self.reader.isOptimized()
        self.close()

        return b

    def last_modified_time (self) :
        self.open_storage()
        try :
            t = datetime.datetime.fromtimestamp(
                lucene.IndexReader.lastModified(self.storage) / 1000
            )
        except lucene.JavaError, e :
            raise constant.StorageException, e

        self.close_storage()
        return t

    def get_document (self, uid) :
        self.open()
        dns = self.reader.termDocs(Term.new(constant.FIELD_NAME_UID, uid))
        if not dns.next() :
            return None

        dn = dns.doc()
        self.close()

        return dn

    def get_field_terms (self, uid, field_name) :
        dn = self.get_document(uid)
        if dn is None :
            return None

        self.open()
        try :
            ts = self.reader.getTermFreqVector(dn, field_name).getTerms()
        except AttributeError :
            ts = None

        self.close()

        return ts

class Term (object) :
    def new (self, field_name, v) :
        return lucene.Term(field_name, v, )

    new        = classmethod(new)

class Field (object) :
    def new (self, field_name, value, store=False, tokenize=False, ) :
        return lucene.Field(
            field_name,
            value,
            store and lucene.Field.Store.YES or lucene.Field.Store.NO,
            tokenize and lucene.Field.Index.TOKENIZED or lucene.Field.Index.UN_TOKENIZED,
            lucene.Field.TermVector.WITH_POSITIONS_OFFSETS,
        )

    new        = classmethod(new)

RegexQuery  = lucene.RegexQuery
RangeQuery  = lucene.RangeQuery

class BooleanQuery (lucene.BooleanQuery) :
    def __init__ (self) :
        super(BooleanQuery, self).__init__()
        self.setMaxClauseCount(constant.MAXINT)

class TermQuery (lucene.PhraseQuery) :
    def __init__ (self, term=None) :
        super(TermQuery, self).__init__()
        if isinstance(term, lucene.Term) :
            for t in term.text().split() :
                self.add(Term.new(term.field(), t))

class Query (lucene.Query) :

    def parse (self, query_string) :
        qparser = lucene.QueryParser("", lucene.WhitespaceAnalyzer())
        qparser.setDefaultOperator(constant.QUERY_OPERATORS.get("AND"))

        # FIXME:it does not work.
        qparser.setLowercaseExpandedTerms(False)

        # Blank query means 'find all the document'.
        try :
            return qparser.parse(query_string)
        except :
            return lucene.MatchAllDocsQuery()

    parse = classmethod(parse)

######################################################################
# Functions
def initialize_vm () :
    lucene.getVMEnv().attachCurrentThread()

def deinitialize_vm () :
    lucene.getVMEnv().detachCurrentThread()

"""
Description
-----------


ChangeLog
---------


Usage
-----


"""

__author__ =  "Spike^ekipS <spikeekips@gmail.com>"
__version__=  "0.1"
__nonsense__ = ""






