"""Plain-HTML bodies for the transactional emails the template sends.

Deliberately string templates, not a rendering engine: a base project should not
force a template stack on every fork. Swap in Jinja here if a project needs it.

TODO: finish after migration — branding, i18n and a plain-text alternative part.
"""

from html import escape


def _wrap(title: str, body: str) -> str:
    return (
        "<html><body style=\"font-family:system-ui,sans-serif;line-height:1.5\">"
        f"<h2>{escape(title)}</h2>{body}</body></html>"
    )


def confirmation_code_email(*, full_name: str, code: str, ttl_minutes: int) -> str:
    return _wrap(
        "Confirm your email",
        f"<p>Hi {escape(full_name)},</p>"
        f"<p>Your confirmation code is <b style='font-size:20px'>{escape(code)}</b>.</p>"
        f"<p>It expires in {ttl_minutes} minutes.</p>",
    )


def password_reset_code_email(*, code: str, ttl_minutes: int) -> str:
    return _wrap(
        "Reset your password",
        f"<p>Your password reset code is <b style='font-size:20px'>{escape(code)}</b>.</p>"
        f"<p>It expires in {ttl_minutes} minutes. If you did not request it, ignore this email.</p>",
    )


def password_changed_email(*, full_name: str) -> str:
    return _wrap(
        "Your password was changed",
        f"<p>Hi {escape(full_name)},</p>"
        "<p>Your password has just been changed. If this was not you, contact support immediately.</p>",
    )
