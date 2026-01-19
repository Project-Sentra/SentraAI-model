"""
Parking System API Client
Communicates with the LPR Parking System backend
"""
import httpx
from typing import Optional
from dataclasses import dataclass

from config import settings


@dataclass
class EntryResult:
    """Result of a vehicle entry request"""
    success: bool
    message: str
    spot_name: Optional[str] = None
    status: Optional[str] = None


@dataclass
class ExitResult:
    """Result of a vehicle exit request"""
    success: bool
    message: str
    duration_minutes: Optional[int] = None
    amount_charged: Optional[int] = None


class ParkingClient:
    """HTTP client for the parking system backend"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.PARKING_API_URL
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=10.0
            )
        return self._client

    async def close(self):
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> bool:
        """Check if the parking backend is reachable"""
        try:
            client = await self._get_client()
            response = await client.get("/api/spots")
            return response.status_code == 200
        except Exception as e:
            print(f"Parking API health check failed: {e}")
            return False

    async def vehicle_entry(self, plate_number: str) -> EntryResult:
        """
        Register a vehicle entry.

        Args:
            plate_number: License plate number

        Returns:
            EntryResult with success status and details
        """
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/vehicle/entry",
                json={"plate_number": plate_number}
            )

            data = response.json()

            if response.status_code == 200:
                return EntryResult(
                    success=True,
                    message=data.get("message", "Entry successful"),
                    spot_name=data.get("spot"),
                    status=data.get("status")
                )
            else:
                return EntryResult(
                    success=False,
                    message=data.get("message", "Entry failed")
                )

        except httpx.RequestError as e:
            return EntryResult(
                success=False,
                message=f"Connection error: {str(e)}"
            )
        except Exception as e:
            return EntryResult(
                success=False,
                message=f"Error: {str(e)}"
            )

    async def vehicle_exit(self, plate_number: str) -> ExitResult:
        """
        Register a vehicle exit.

        Args:
            plate_number: License plate number

        Returns:
            ExitResult with success status and billing details
        """
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/vehicle/exit",
                json={"plate_number": plate_number}
            )

            data = response.json()

            if response.status_code == 200:
                return ExitResult(
                    success=True,
                    message=data.get("message", "Exit successful"),
                    duration_minutes=data.get("duration_minutes"),
                    amount_charged=data.get("amount_charged")
                )
            else:
                return ExitResult(
                    success=False,
                    message=data.get("message", "Exit failed")
                )

        except httpx.RequestError as e:
            return ExitResult(
                success=False,
                message=f"Connection error: {str(e)}"
            )
        except Exception as e:
            return ExitResult(
                success=False,
                message=f"Error: {str(e)}"
            )

    async def get_spots(self) -> list[dict]:
        """Get all parking spots"""
        try:
            client = await self._get_client()
            response = await client.get("/api/spots")

            if response.status_code == 200:
                data = response.json()
                return data.get("spots", [])
            return []

        except Exception as e:
            print(f"Error fetching spots: {e}")
            return []

    async def get_logs(self, limit: int = 50) -> list[dict]:
        """Get recent parking logs"""
        try:
            client = await self._get_client()
            response = await client.get("/api/logs")

            if response.status_code == 200:
                data = response.json()
                return data.get("logs", [])[:limit]
            return []

        except Exception as e:
            print(f"Error fetching logs: {e}")
            return []


# Singleton instance
parking_client = ParkingClient()
