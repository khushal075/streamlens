from enum import Enum

class LogSource(str, Enum):
    NGINX = "nginx"
    POSTGRES = "postgresql"
    K8S = "kubernetes"
    SYSLOG = "syslog"
    GENERIC = "generic"

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"