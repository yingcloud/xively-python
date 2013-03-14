# -*- coding: utf-8 -*-

__title__ = 'cosm-python'
__version__ = '0.1.0'

try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin  # NOQA


__all__ = ['Feed', 'Datastream', 'Datapoint', 'Location', 'Waypoint',
           'Trigger', 'Key', 'Permission', 'Resource']


class Base(object):
    """Abstract base class to store API data and allow (de)serialisation."""

    def __init__(self):
        self._data = {}

    def __getstate__(self):
        return dict(**self._data)

    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError:
            class_name = self.__class__.__name__
            raise AttributeError(
                "'{}' object has no attribute '{}'".format(class_name, name))

    def __setattr__(self, name, value):
        if not name.startswith('_') and name not in dir(self.__class__):
            self._data[name] = value
        else:
            super(Base, self).__setattr__(name, value)


class Feed(Base):
    """Cosm Feed, which can contain a number of Datastreams."""

    VERSION = "1.0.0"

    _datastreams = None

    def __init__(self, title, **kwargs):
        self._data = {
            'title': title,
            'version': self.VERSION,
        }
        if 'datastreams' in kwargs:
            self.datastreams = kwargs.pop('datastreams')
        self._data.update(kwargs)

    @property
    def datastreams(self):
        if self._datastreams is None:
            import cosm.api
            self._datastreams = cosm.api.DatastreamsManager(self)
        return self._datastreams

    @datastreams.setter  # NOQA
    def datastreams(self, datastreams):
        manager = getattr(self, '_manager', None)
        if manager:
            manager._coerce_datastreams(self.datastreams, datastreams)
        self._data['datastreams'] = datastreams

    def update(self, fields=None):
        url = self.feed
        state = self.__getstate__()
        if fields is not None:
            fields = set(fields)
            state = {k: v for k, v in state.items() if k in fields}
        self._manager.update(url, **state)

    def delete(self):
        url = self.feed
        self._manager.delete(url)


class Datastream(Base):
    """Cosm Datastream containing current and historical values."""

    _datapoints = None

    def __init__(self, id, **kwargs):
        self._data = {'id': id}
        self.datapoints = kwargs.pop('datapoints', [])
        self._data.update(**kwargs)

    def __getstate__(self):
        state = super(Datastream, self).__getstate__()
        if not state['datapoints']:
            state.pop('datapoints')
        return state

    @property
    def datapoints(self):
        if self._datapoints is None:
            import cosm.api
            self._datapoints = cosm.api.DatapointsManager(self)
        return self._datapoints

    @datapoints.setter  # NOQA
    def datapoints(self, datapoints):
        self._data['datapoints'] = datapoints

    def update(self, fields=None):
        state = self.__getstate__()
        if fields is not None:
            fields = set(fields)
            state = {k: v for k, v in state.items() if k in fields}
        self._manager.update(self.id, **state)

    def delete(self):
        self._manager.delete(self.id)


class Datapoint(Base):
    """A Datapoint represents a value at a certain point in time."""

    def __init__(self, at, value):
        super(Datapoint, self).__init__()
        self._data['at'] = at
        self._data['value'] = value

    def update(self):
        state = self.__getstate__()
        self._manager.update(state.pop('at'), **state)

    def delete(self):
        self._manager.delete(self.at)


class Location(Base):

    def __init__(self, name=None, domain=None, exposure=None, disposition=None,
                 lat=None, lon=None, ele=None, waypoints=None):
        self._data = {
            'name': name,
            'domain': domain,
            'exposure': exposure,
            'disposition': disposition,
            'lat': lat,
            'lon': lon,
            'ele': ele,
        }
        if waypoints is not None:
            self._data['waypoints'] = waypoints

    def __getstate__(self):
        state = super(Location, self).__getstate__()
        return {k: v for (k, v) in state.items() if v is not None}


class Waypoint(Base):
    """A location waypoint."""

    def __init__(self, at, lat, lon):
        """Create a location waypoint, a timestamped cordinate pair."""
        self._data = {
            'at': at,
            'lat': lat,
            'lon': lon,
        }


class Trigger(Base):
    """Triggers provide 'push' capabilities (aka notifications)."""

    def __init__(self, environment_id, stream_id, url, trigger_type,
                 threshold_value=None, **kwargs):
        self._data = {
            'environment_id': environment_id,
            'stream_id': stream_id,
            'url': url,
            'trigger_type': trigger_type,
        }
        if threshold_value is not None:
            self._data['threshold_value'] = threshold_value
        self._data.update(kwargs)

    def update(self, fields=None):
        state = self.__getstate__()
        state.pop('id', None)
        if fields is not None:
            fields = set(fields)
            state = {k: v for k, v in state.items() if k in fields}
        self._manager.update(self.id, **state)

    def delete(self):
        self._manager.delete(self.id)


class Key(Base):
    """Keys set which permissions are granted for certain resources."""

    def __init__(self, label, permissions, expires_at=None,
                 private_access=False):
        self._data = {
            'label': label,
            'permissions': permissions,
            'private_access': private_access,
        }
        if expires_at:
            self._data['expires_at'] = expires_at

    def delete(self):
        self._manager.delete(self.api_key)


class Permission(Base):

    def __init__(self, access_methods, source_ip=None, referer=None,
                 minimum_interval=None, label=None, resources=None):
        self._data = {
            'access_methods': access_methods,
        }
        self._data.update((name, value) for (name, value) in (
            ('source_ip', source_ip),
            ('referer', referer),
            ('minimum_interval', minimum_interval),
            ('label', label),
            ('resources', resources),
        ) if value is not None)


class Resource(Base):

    def __init__(self, feed_id, datastream_id=None):
        self._data = {
            'feed_id': feed_id,
        }
        if datastream_id:
            self._data['datastream_id'] = datastream_id
