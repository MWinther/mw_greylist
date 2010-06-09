    def _test_rbl_server(self, server_name):
        if 'client_address' in self.headers:
            res = rbl.check_rbl_like(self.headers['client_address'],
                                       root_name=server_name)
            self.rbl_results[server_name] = res
            self._write_to_syslog("RBL check for server %s returns %s" % (server_name, res))
            return res
        else:
            self._write_to_syslog(LOG_WARN, "No client_address in headers.")
            raise GLIncompleteHeaderException, "No client address in headers."
            return None

    def test_rbl(self):
        try:
            servers = self.config.get('test_settings', 'rbl_servers')
        except NoOptionError:
            self._write_to_syslog(LOG_INFO, "No RBL servers, ignoring test")
            return None
        for server in servers.split('\n'):
            self._test_rbl_server(server)

    def rbl_score(self):
        score = 0
        for server in self.rbl_results.keys():
            if self.rbl_results[server]:
                score = score + 1
        return score
