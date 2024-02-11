from sqlalchemy.orm import session


class ScopedSessionContainer(object):
    scoped_session = None
    _sessions = session._sessions


def _state_session(state):
    if state.obj() and getattr(state.obj(), "always_use_scoped_session", False):
        return ScopedSessionContainer.scoped_session()
    if state.session_id:
        try:
            return ScopedSessionContainer._sessions[state.session_id]
        except KeyError:
            pass
    return None


def patch_alchemy(scoped_session=None):
    session._state_session.__code__ = _state_session.__code__
    session.ScopedSessionContainer = ScopedSessionContainer
    if scoped_session is not None:
        ScopedSessionContainer.scoped_session = scoped_session
