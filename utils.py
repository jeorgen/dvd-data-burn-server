import sys

def missing_or_bad_config(e, attempted_file, example_file):
    sys.stderr.write( """
        ERROR: "%s" in config file '%s'

        Does the file exist and does it have the right sections?
        Copy the file "%s" to %s for correct format
        and edit that file to your liking

        """  % (e, attempted_file, example_file, attempted_file) )
    print
    sys.exit()  

class ModuleAttributesContextManager(object):
    """ Used in testing """

    def __init__(self, module, values):
        self.module = module
        self.values = values

    def __enter__(self):
        self.saved_values = {}
        for key, value in self.values.items():
            self.saved_values[key] = getattr(self.module, key)
            setattr(self.module, key, value)

    def __exit__(self, exc_type, exc_value, traceback):
        for key, value in self.saved_values.items():
            setattr(self.module, key, value)