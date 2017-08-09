# coding=utf-8
from __future__ import unicode_literals

"""
Copyright 2009 55 Minutes (http://www.55minutes.com)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""
import os
import sys

import django
import coverage
if django.VERSION < (1, 8):
    msg = """

    django-coverage 1.3+ requires django 1.8+.
    Please use django-coverage 1.0.3 if you have django 1.1 or django 1.0
    """
    raise Exception(msg)


from django.conf import global_settings
from django.test.utils import get_runner
from django_coverage import settings
from django_coverage.utils.coverage_report import html_report


DjangoTestSuiteRunner = get_runner(global_settings)


class CoverageRunner(DjangoTestSuiteRunner):
    """
    Test runner which displays a code coverage report at the end of the run.
    """

    raise_exception = getattr(settings, 'COVERAGE_MINI_RAISE_EXCEPTION', None)
    mini_cover = getattr(settings, 'COVERAGE_MINI_COVER', 0)
    coverage_source = getattr(settings, 'COVERAGE_SOURCE', None)

    def __new__(cls, *args, **kwargs):
        """
        Add the original test runner to the front of CoverageRunner's bases,
        so that CoverageRunner will inherit from it. This allows it to work
        with customized test runners.
        """
        # If the test runner was changed by the management command, change it
        # back to its original value in order to get the original runner.
        if getattr(settings, 'ORIG_TEST_RUNNER', None):
            settings.TEST_RUNNER = settings.ORIG_TEST_RUNNER
            TestRunner = get_runner(settings)
            if (TestRunner != DjangoTestSuiteRunner):
                cls.__bases__ = (TestRunner,) + cls.__bases__
        return super(CoverageRunner, cls).__new__(cls)

    def _get_app_package(self, app_model_module):
        """
        Returns the app module name from the app model module.
        """
        return '.'.join(app_model_module.__name__.split('.')[:-1])

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        pc_covered = 0
        self.cov = coverage.Coverage(source=self.coverage_source)
        for e in settings.COVERAGE_CODE_EXCLUDES:
            self.cov.exclude(e)
        self.cov.start()
        results = super(CoverageRunner, self).run_tests(test_labels,
                                                        extra_tests, **kwargs)
        self.cov.stop()

        if settings.COVERAGE_USE_STDOUT:
            pc_covered = self.cov.report(show_missing=1)

        outdir = settings.COVERAGE_REPORT_HTML_OUTPUT_DIR
        if outdir:
            outdir = os.path.abspath(outdir)
            pc_covered = self.cov.html_report(directory=outdir)
            print("HTML reports were output to '%s'" %outdir)

        # print ("coverage_source is {}".format(self.coverage_source))
        if self.raise_exception and pc_covered < self.mini_cover:
            print ("covered must >= {}".format(self.mini_cover))
            sys.exit(1)

        return results
