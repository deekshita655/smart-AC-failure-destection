import enum


class RoleEnum(str, enum.Enum):
    TECHNICIAN = "TECHNICIAN"
    OVERALL_MANAGEMENT = "OVERALL_MANAGEMENT"
    QUALITY = "QUALITY"
    DESIGN = "DESIGN"
    ADMIN = "ADMIN"


class TicketStatus(str, enum.Enum):
    OPEN = "OPEN"
    ANALYZED = "ANALYZED"
    COMPLETED = "COMPLETED"


class PreventiveTicketStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    LINKED_TO_SERVICE = "LINKED_TO_SERVICE"
    CLOSED = "CLOSED"


class DeviceHealthStatus(str, enum.Enum):
    HEALTHY = "HEALTHY"
    DEGRADING = "DEGRADING"
    ANOMALOUS = "ANOMALOUS"
    CRITICAL = "CRITICAL"
