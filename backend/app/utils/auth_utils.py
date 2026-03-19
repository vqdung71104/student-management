from fastapi import HTTPException, status


def _auth_disabled_error() -> None:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="auth_utils is deprecated. Use JWT dependencies in app.utils.jwt_utils instead.",
    )


def get_current_student_id(*args, **kwargs):
    _auth_disabled_error()


def get_current_admin(*args, **kwargs):
    _auth_disabled_error()


def get_current_user(*args, **kwargs):
    _auth_disabled_error()