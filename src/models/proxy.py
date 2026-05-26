from typing import Any, Literal
from urllib.parse import urlparse
from pydantic import BaseModel, Field, model_validator

ProxyType = Literal["http", "https", "socks5", "ssh"]

class Proxy(BaseModel):
    model_config = {"frozen": True}
    host: str = Field(min_length=1)
    port: int = Field(gt=0, le=65535)
    user: str = ""
    password: str = ""
    type: ProxyType = "http"

    @classmethod
    def from_url(cls, url: str) -> "Proxy": return cls.model_validate(url)

    @model_validator(mode="before")
    @classmethod
    def parse_url(cls, data: Any) -> Any:
        if isinstance(data, str):
            u = urlparse(data)
            return {"host": u.hostname or "", "port": u.port or 0, "user": u.username or "",
                    "password": u.password or "", "type": u.scheme or "http"}
        return data

    def __str__(self) -> str:
        if self.user: return f"{self.type}://{self.user}:{self.password}@{self.host}:{self.port}"
        return f"{self.type}://{self.host}:{self.port}"

    def __repr__(self) -> str: return f"<Proxy {self.host}:{self.port}>"
