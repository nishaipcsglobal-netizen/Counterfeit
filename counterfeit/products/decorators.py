# FILE: products/decorators.py
from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

F = TypeVar("F", bound=Callable[..., HttpResponse])


def role_required(role: str, *, allow_superuser: bool = True) -> Callable[[F], F]:
    def _decorator(view_func: F) -> F:
        @wraps(view_func)
        def _wrapped(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
            user = getattr(request, "user", None)
            if not user or not user.is_authenticated:
                return redirect("login")

            if allow_superuser and (user.is_superuser or user.is_staff):
                return view_func(request, *args, **kwargs)

            if getattr(user, "role", None) != role:
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return _wrapped  # type: ignore[return-value]

    return _decorator