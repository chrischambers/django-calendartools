class SimpleProxy(object):
    def __init__(self, obj, *args, **kwargs):
        self._obj = obj
        super(SimpleProxy, self).__init__(*args, **kwargs)

    def __cmp__(self, other):
        return cmp(self._obj, other)

    def __add__(self, other):
        return self._obj + other

    def __sub__(self, other):
        return self._obj - other

    def __unicode__(self):
        return unicode(self._obj)

    def __repr__(self):
        try:
            u = unicode(self)
        except (UnicodeEncodeError, UnicodeDecodeError):
            u = '[Bad Unicode data]'
        return (u'<%s: %s>' % (self.__class__.__name__, u)).encode('utf8')

    def __getattr__(self, attr):
        """Issue: Test Methods like assert_raises and self.assertRaises won't
        catch the AttributeError raised here."""
        try:
            return getattr(self.__class__, attr)
        except AttributeError:
            try:
                return getattr(self._obj, attr)
            except AttributeError, e:
                e = "%r and its Proxy(%r) have no '%s' attributes." % (
                    self._obj, self, attr
                )
                raise AttributeError, e
