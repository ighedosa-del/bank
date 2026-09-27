"""Scenario adapter. This application never connects to a real bank."""
class BankBot:
    def __init__(self, bank_name: str):
        if bank_name not in {"gtbank", "uba"}:
            raise ValueError("Unsupported simulated bank")
        self.bank_name = bank_name

    def transfer(self, target_account: str, amount: str) -> str:
        return "OTP Required — simulation only"
