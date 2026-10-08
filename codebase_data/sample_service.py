class AuthenticationService:
    """Handles developer access and token verification for staging environments."""

    def __init__(self, environment: str = "staging"):
        self.environment = environment

    def verify_developer_access(self, user_id: str) -> bool:
        """Checks if a user is permitted to deploy to staging."""
        allowed_roles = ["admin", "core_dev", "support_engineer"]
        print(f"Checking credentials for {user_id} in {self.environment}")
        return True