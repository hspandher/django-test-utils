# inbuilt python imports
import os
import shutil

# inbuild django imports
from django.http import HttpRequest
from django.conf import settings
from django.utils.module_loading import import_module

# third-party django imports
from mongoengine.connection import (DEFAULT_CONNECTION_NAME, _connections, get_connection,
                                    _dbs)


# inter-app imports

# local imports

class EnhancedHttpRequest(HttpRequest):
    def __init__(self, method='GET'):
        super(EnhancedHttpRequest, self).__init__()
        self.method = method

        session_engine = import_module(settings.SESSION_ENGINE)
        self.session = session_engine.SessionStore(session_key=None)


class TestViewMixin(object):
    def create_view_object(self, view, request, args=[], kwargs={}):
        view_object = view()
        view_object.request, view_object.args, view_object.kwargs = request, args, kwargs

        return view_object


class ClearFileStorageMixin(object):
    TEST_STORAGE_DIRECTORY = None

    def tearDown(self):
        if self.TEST_STORAGE_DIRECTORY:
            shutil.rmtree(self.TEST_STORAGE_DIRECTORY, ignore_errors=True)
            os.makedirs(self.TEST_STORAGE_DIRECTORY)

    @classmethod
    def tearDownAll(cls):
        if cls.TEST_STORAGE_DIRECTORY:
            shutil.rmtree(cls.TEST_STORAGE_DIRECTORY, ignore_errors=True)
            os.makedirs(cls.TEST_STORAGE_DIRECTORY)


class CopyLargeFileMixin(ClearFileStorageMixin):
    """
    This is a mixin inheriting ClearFileStorageMixin to
    copy the larger files which you cannot keep inside
    a github project because of size constraints, for eg.
    Large video files which you might need for testing.
    A better approach is to copy the file each time you
    run the test from your computer to the TEST_STORAGE_DIRECTORY
    and delete it after each test run.
    """

    STORED_FILE_PATH = None
    TEST_STORAGE_DIRECTORY = None

    def tearDown(self):
        if not self.STORED_FILE_PATH:
            return super(CopyLargeFileMixin, self).tearDown()

        super(CopyLargeFileMixin, self).tearDown()
        shutil.copy(self.STORED_FILE_PATH, self.TEST_STORAGE_DIRECTORY)

    @classmethod
    def tearDownAll(cls):
        if not cls.STORED_FILE_PATH:
            return super(CopyLargeFileMixin, cls).tearDownAll()

        super(CopyLargeFileMixin, cls).tearDownAll()
        shutil.copy(cls.STORED_FILE_PATH, cls.TEST_STORAGE_DIRECTORY)


class ModifySessionMixin(object):
    def create_session(self):
        session_engine = import_module(settings.SESSION_ENGINE)
        store = session_engine.SessionStore()
        store.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key


def disconnect(alias=DEFAULT_CONNECTION_NAME):
    """ To disconnect pymongo connection.

    Copied from mongoengine/connection.py to fix a bug in mongoengine source code,
    ('disconnect' method is removed from pymongo MongoClient in latest version.)
    """
    global _connections
    global _dbs

    if alias in _connections:
        get_connection(alias=alias).close()
        del _connections[alias]
    if alias in _dbs:
        del _dbs[alias]
