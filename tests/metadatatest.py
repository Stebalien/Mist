import os
import random
import unittest
import metaedit

modulePath = os.path.dirname(os.path.abspath(__file__))
sampleMP3Path = os.path.join(modulePath, "sample.mp3")
sampleM4APath = os.path.join(modulePath, "sample.m4a")
randomNumber = random.randint(0, 100)

class SimpleMP3TestCase(unittest.TestCase):
    def setUp(self):
        self.fileMetadataHandler = metaedit.metadataHandler(sampleMP3Path)
        
class SimpleM4ATestCase(unittest.TestCase):
    def setUp(self):
        self.fileMetadataHandler = metaedit.metadataHandler(sampleM4APath)
        
class basicMP3MetadataTest(SimpleMP3TestCase):
    def runTest(self):
        self.fileMetadataHandler.write({"title":"Testing {}".format(randomNumber)})
        assert self.fileMetadataHandler.read(["TITLE"])[0]["TITLE"] == "Testing {}" \
                    .format(randomNumber)
    
class basicM4AMetadataTest(SimpleM4ATestCase):
    def runTest(self):
        self.fileMetadataHandler.write({"title":"Testing {}".format(randomNumber)})
        assert self.fileMetadataHandler.read(["TITLE"])[0]["TITLE"] == "Testing {}" \
                .format(randomNumber)
    
