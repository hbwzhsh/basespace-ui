from jobserver.tasks import mkpath
import peakAnalyzer.settings.ROOT_DIR
import os
#create tmp dir


_TMP_DIR = os.path.join(peakAnalyzer.settings.ROOT_DIR, 'tmp')
mkpath(_TMP_DIR)