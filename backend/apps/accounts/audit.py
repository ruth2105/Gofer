from apps.accounts.models import SecurityAuditEvent


def record_security_event(action, *, actor=None, target=None, details=None):
    return SecurityAuditEvent.objects.create(
        action=action,
        actor=actor,
        actor_role=actor.role if actor else '',
        target=target,
        target_role=target.role if target else '',
        details=details or {},
    )
