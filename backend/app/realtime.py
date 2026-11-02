from flask import request
from flask_jwt_extended import decode_token
from flask_socketio import SocketIO, emit, join_room, leave_room

from app import db
from app.models import User
from app.security import is_token_revoked

# Rooms
ROOM_ALL = "alerts:all"              # everyone with dashboard open
ROOM_ADMINS = "alerts:admins"        # admin-only alerts
ROOM_SALES = "alerts:sales"          # new enquiries, bookings
ROOM_OPS = "alerts:ops"              # operational events


def user_room(user_id) -> str:
    return f"user:{user_id}"


def register_socket_events(socketio: SocketIO):
    @socketio.on("connect")
    def on_connect(auth):
        token = (auth or {}).get("token")
        if not token:
            return False
        try:
            data = decode_token(token)
            user = db.session.get(User, data["sub"])
            if (
                not user
                or not user.is_active
                or int(data.get("tv", 0)) != int(user.token_version or 0)
                or is_token_revoked({}, data)
            ):
                return False
        except Exception:
            return False

        join_room(user_room(user.id))
        join_room(ROOM_ALL)

        if user.has_permission("alert.admin"):
            join_room(ROOM_ADMINS)


        emit("connected", {"user_id": str(user.id)})

    @socketio.on("disconnect")
    def on_disconnect():
        # socketio handles room cleanup automatically on disconnect
        pass

    @socketio.on("ping:client")
    def on_ping():
        emit("pong:server", {"ts": __import__("time").time()})


# ─── Emit helpers (called from API routes or Celery tasks) ───

def emit_alert(event: str, payload: dict, room: str = ROOM_ALL):
    """
    Fire an internal alert over WebSocket.

    Safe to call from:
      • Flask request handlers
      • Celery workers (as long as SOCKETIO_MESSAGE_QUEUE is set)

    Never raises — if the socket layer is down, the business action
    still succeeds.
    """
    from app import socketio
    try:
        socketio.emit(event, payload, to=room)
    except Exception as e:
        from app.errors import log  # or your logger
        log.warning("emit_alert_failed", event=event, room=room, error=str(e))




def emit_to_user(user_id, event: str, payload: dict):
    emit_alert(event, payload, room=user_room(user_id))