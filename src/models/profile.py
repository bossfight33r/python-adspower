from pydantic import BaseModel, Field
from .proxy import Proxy

class Profile(BaseModel):
    model_config = {"frozen": True}
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    remark: str = ""
    group: str = ""
    proxy: Proxy | None = None

    @property
    def label(self) -> str: return self.remark or self.name or self.id
    def __repr__(self) -> str:
        p = f" proxy={self.proxy.host}" if self.proxy else ""
        return f"<Profile id={self.id!r} label={self.label!r}{p}>"

class ActiveProfile(Profile):
    websocket_url: str = Field(min_length=1)
    debug_port: int = Field(ge=0)
    def __repr__(self) -> str:
        return f"<ActiveProfile id={self.id!r} label={self.label!r} port={self.debug_port}>"
