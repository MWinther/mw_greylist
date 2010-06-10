from mw_greylist.pluginframework import ActionProvider
from mw_greylist.exceptions import *
from mw_greylist.log import Log
from syslog import *
from mw_greylist.plugins.rbl import check_rbl_like
from ConfigParser import NoOptionError, NoSectionError

class RBL(ActionProvider):

    def __init__(self, headers={}, settings=None):
        self.headers = headers
        self.settings = settings
        self.servers = self._get_servers()
        self.results = {}

    def __repr__(self):
        return "RBL plugin v1.0b for mw_greylist"

    def _get_servers(self):
        try:
            servers = self.settings.file_settings.get('rbl_plugin', 'rbl_servers')
        except AttributeError:
            self.results = None
        except NoOptionError:
            log.write("No RBL servers in config file, ignoring test.", LOG_WARNING)
            self.results = None
        except NoSectionError:
            log.write("No RBL section in config file, ignoring test.", LOG_WARNING)
            self.results = None
        else:
            server_list = []
            for server in servers.split('\n'):
                server_list.append(server)
            return server_list
        return None


    def do_test(self):
        if self.servers:
            for server in self.servers:
                self._test_rbl_server(server)

    def _test_rbl_server(self, server_name):
        if 'client_address' in self.headers:
            res = check_rbl_like(self.headers['client_address'],
                                 root_name=server_name)
            self.results[server_name] = res
            log.write("RBL check for server %s returns %s"\
                        % (server_name, res), LOG_DEBUG)
            return res
        else:
            log.write("No client address in headers.", LOG_WARNING)
            raise GLIncompleteHeaderException, "No client address in headers."
            return None

    def get_score(self):
        score = 0
        if self.results == None or self.results == {}:
            return None
        for server in self.results.keys():
            if self.results[server]:
                score = score + 1
        log.write("RBL score: %d" % score, LOG_DEBUG)
        return score

log = Log()
