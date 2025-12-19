from io import BytesIO
from typing import Literal

from fastapi import UploadFile
from pypdf import PdfReader


SupportedExt = Literal["pdf", "txt"]


MAX_TEXT_LENGTH = 15_000


def _truncate(text: str, max_length: int = MAX_TEXT_LENGTH) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length]


def _extract_from_pdf(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    chunks: list[str] = []
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
        if page_text:
            chunks.append(page_text)
    return _truncate("\n".join(chunks))


def _extract_from_txt(data: bytes) -> str:
    text = data.decode("utf-8", errors="ignore")
    return _truncate(text)


def detect_extension(filename: str | None) -> SupportedExt | None:
    if not filename:
        return None
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return "pdf"
    if lower.endswith(".txt"):
        return "txt"
    return None


async def extract_text_from_upload(file: UploadFile) -> str:
    """
    업로드된 파일(메모리 상)의 내용을 텍스트로 추출한다.

    - PDF: pypdf로 텍스트 추출
    - TXT: UTF-8로 디코딩
    - 최대 길이: 15,000자
    """
    ext = detect_extension(file.filename)
    if ext is None:
        raise ValueError("지원하지 않는 파일 형식입니다. pdf 또는 txt만 업로드해 주세요.")

    data = await file.read()
    if not data:
        raise ValueError("빈 파일이거나 내용을 읽을 수 없습니다.")

    if ext == "pdf":
        text = _extract_from_pdf(data)
    elif ext == "txt":
        text = _extract_from_txt(data)
    else:
        # 타입 가드용, 실제로는 도달하지 않음
        raise ValueError("지원하지 않는 파일 형식입니다.")

    if not text.strip():
        raise ValueError("파일에서 텍스트를 추출할 수 없습니다.")

    return text


