from sqlalchemy.orm import session


class ScopedSessionContainer(object):
    scoped_session = None


def _state_session(state):
    if state.obj() and getattr(state.obj(), 'always_use_scoped_session', False):
        return ScopedSessionContainer.scoped_session()
    if state.session_id:
        try:
            return session._sessions[state.session_id]
        except KeyError:
            pass
    return None


def patch_alchemy():
    session._state_session.__code__ = _state_session.__code__
    session.ScopedSessionContainer = ScopedSessionContainer