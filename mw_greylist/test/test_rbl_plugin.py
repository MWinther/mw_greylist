    def testRBLCheckWithoutClient(self):
        self.failUnlessRaises(Exception,
                              self.glc._test_rbl_server,
                              'zen.spamhaus.org')

    def testRBLServerResponse(self):
        self.glc.headers['client_address'] = '127.0.0.2'
        self.assertNotEqual(None,
                            self.glc._test_rbl_server('zen.spamhaus.org'))

    def testRBLServerResponseStoredCorrectly(self):
        self.glc.headers['client_address'] = '127.0.0.2'
        self.glc._test_rbl_server('zen.spamhaus.org')
        self.assert_('zen.spamhaus.org' in self.glc.rbl_results)

if __name__ == '__main__':
    unittest.main()
