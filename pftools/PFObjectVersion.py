from pydantic import BaseModel

class _ObjectVersion(BaseModel):
    WriteVersion = ''
    CreateVersion = ''
    CreateTimeStamp = ''
    WriteTimeStamp = ''
    LastModifiedTimeStamp = ''

