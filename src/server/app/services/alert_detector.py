import yaml
from pathlib import Path
from ..models import Alert

# Chargement des seuils depuis config/thresholds.yaml
_thresholds = yaml.safe_load(
    Path("config/thresholds.yaml").read_text()
)

def detect_alerts(metric) -> list[Alert]:
    alerts = []
    checks = [
        ("cpu", metric.cpu_percent),
        ("memory", metric.memory_percent),
        ("disk", metric.disk_percent),
    ]
    for name, value in checks:
        t = _thresholds.get(name, {})
        if value >= t.get("critical", 95):
            level = "critical"
        elif value >= t.get("warning", 80):
            level = "warning"
        else:
            continue
        alerts.append(Alert(
            node_id=metric.node_id, level=level,
            metric=name, value=value,
            message=f"{name} à {value:.1f}% ({level})"
        ))
    return alerts