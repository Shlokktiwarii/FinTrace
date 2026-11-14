from functools import lru_cache

from supabase import Client, create_client

from fintrace.core.config import get_settings


@lru_cache
def get_supabase_client() -> Client:
    settings = get_settings()

    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("Supabase storage credentials are not configured.")

    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )


class SupabaseStorage:
    def __init__(self) -> None:
        settings = get_settings()

        self.client = get_supabase_client()
        self.bucket = settings.supabase_storage_bucket

    def upload(self, path: str, content: bytes) -> None:
        self.client.storage.from_(self.bucket).upload(
            path,
            content,
            file_options={
                "content-type": "application/pdf",
                "upsert": "false",
            },
        )

    def download(self, path: str) -> bytes:
        return self.client.storage.from_(self.bucket).download(path)

    def delete(self, path: str) -> None:
        self.client.storage.from_(self.bucket).remove([path])