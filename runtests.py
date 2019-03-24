import sys
import django
from django.test.runner import DiscoverRunner

django.setup()
test_runner = DiscoverRunner(verbosity=1)

failures = test_runner.run_tests(['tests'])
if failures:
    sys.exit(failures)
