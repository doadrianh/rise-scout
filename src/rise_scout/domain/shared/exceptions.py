class DomainError(Exception):
    pass


class ContactNotFoundError(DomainError):
    def __init__(self, contact_id: str) -> None:
        super().__init__(f"Contact {contact_id} not found")
        self.contact_id = contact_id


class InvalidSignalError(DomainError):
    def __init__(self, signal: str, reason: str) -> None:
        super().__init__(f"Invalid signal {signal}: {reason}")
        self.signal = signal


class StaleContactError(DomainError):
    def __init__(self, contact_id: str) -> None:
        super().__init__(f"Contact {contact_id} has been modified concurrently")
        self.contact_id = contact_id
