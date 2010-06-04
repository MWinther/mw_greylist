from mw_greylist.pluginframework import ActionProvider

class RBL(ActionProvider):

    @staticmethod
    def do_test(headers):
        print "Do RBL test on ", headers
        return 1
