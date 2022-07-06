from pydantic import BaseModel

__all__ = ["JMAList"]


class JMAListAuthor(BaseModel):
    name: str


class JMAListContent(BaseModel):
    text: str
    type: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "text": "#text",
            "type": "@type"
        }


class JMAListEntryLink(BaseModel):
    href: str
    type: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "href": "@href",
            "type": "@type"
        }


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
