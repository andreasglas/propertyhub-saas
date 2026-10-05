def build_pagination(page: int = 1, page_size: int = 25) -> dict[str, int]:
    return {"page": page, "page_size": page_size}
