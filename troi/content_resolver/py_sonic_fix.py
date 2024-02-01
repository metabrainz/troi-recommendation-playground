from libsonic import Connection


class FixedConnection(Connection):
    """
        This hack enables album ids to strings -- a PR has been submitted, but in case
        it doesn't get accepted in a timely manner, this workaround allows us to 
        continue.
    """

    def getAlbumInfo2(self, aid):
        """
        since 1.14.0

        Same as getAlbumInfo, but uses ID3 tags

        aid:int     The album ID    
        """
        methodName = 'getAlbumInfo2'
        viewName = '%s.view' % methodName

        # The release version has an int() cast here
        q = {'id': aid}
        req = self._getRequest(viewName, q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res
