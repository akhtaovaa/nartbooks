"""Enumerations used across the project."""

from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

