from pydantic import ConfigDict, BaseModel, Field

__all__ = ["JMAList"]


class JMAListAuthor(BaseModel):
    name: str


class JMAListContent(BaseModel):
    text: str = Field(validation_alias="#text")
    type: str = Field(validation_alias="@type")
    model_config = ConfigDict(populate_by_name=True)


class JMAListEntryLink(BaseModel):
    href: str = Field(validation_alias="@href")
    type: str = Field(validation_alias="@type")
    model_config = ConfigDict(populate_by_name=True)


class JMAListEntry(BaseModel):
    author: JMAListAuthor
    content: JMAListContent
    id: str
    link: JMAListEntryLink
    title: str
    updated: str


class JMAListFeed(BaseModel):
    entry: list[JMAListEntry]
    id: str
    title: str
    updated: str


class JMAList(BaseModel):
    feed: JMAListFeed
