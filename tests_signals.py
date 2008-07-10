# -*- coding: utf-8 -*-
#	Copyright 2005,2006,2007,2008 Spike^ekipS <spikeekips@gmail.com>
#
#	   This program is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; either version 2 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import unittest, sys, datetime, random

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import models as models_auth
from django.contrib.webdesign.lorem_ipsum import words, paragraphs
from django.db import models

import core, pylucene

import _tests

class SignalsTestCase (unittest.TestCase):
	def setUp (self) :
		self.from_model = _tests.document.objects
		self.from_indexed = _tests.document.objects_search

	def testCreateObject (self) :
		o = _tests.document.objects.create(
			title=words(5, False),
			content=paragraphs(1, False)[0],
			summary=paragraphs(1, False)[0],
			time_added=datetime.datetime.now() - datetime.timedelta(days=int(random.random() * 10)),
			path="/home/dir.com/" + str(random.random() * 1000) + "/",
		)

		o_n = self.from_indexed.get(pk=o.pk)

		self.assertEquals(o.pk, o_n.get("__pk__"))
		self.assertEquals(o.title, o_n.get("title"))
		self.assertEquals(o.summary, o_n.get("summary"))
		self.assertEquals(
			core.DocumentValue.to_index("date",o.time_added),
			core.DocumentValue.to_index("date", o_n.get("time_added")),
		)

	def testDeleteObjectFromModel (self) :
		obj = self.from_model.all()[0]
		pk = obj.pk

		obj.delete()

		self.assertRaises(ObjectDoesNotExist, self.from_indexed.get, pk=pk)

	def testUpdate (self) :
		obj = self.from_model.all()[0]

		o_n0 = self.from_indexed.get(pk=obj.pk)

		obj.title = obj.title + str(random.random() * 10)
		obj.save()

		o_n1 = self.from_indexed.get(pk=obj.pk)

		self.assertEquals(obj.title, o_n1.get("title"))

if __name__ == "__main__" :
	import sys
	import _tests

	settings.SEARCH_STORAGE_PATH = settings.SEARCH_STORAGE_PATH  + "_test"
	settings.SEARCH_STORAGE_TYPE = "fs"
	#settings.DEBUG = 2

	_tests.cleanup_index()
	_tests.cleanup_documents()
	_tests.insert_documents(10)

	unittest.main(testRunner=_tests.SearcherTestRunner(verbosity=2))
	sys.exit()



"""
Description
-----------


ChangeLog
---------


Usage
-----


"""

__author__ =  "Spike^ekipS <spikeekips@gmail.com>"




