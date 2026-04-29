from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        error_type: str,
        code: str,
        message: str,
    ) -> None:
        self.status_code = status_code
        self.error_type = error_type
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class EmbeddingRequest:
    model: str
    input: str
    encoding_format: str

    def to_upstream_payload(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "input": self.input,
            "encoding_format": self.encoding_format,
        }


def error_response(error: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "type": error.error_type,
                "code": error.code,
                "message": error.message,
            }
        },
    )


def openai_error(
    status_code: int,
    code: str,
    message: str,
    error_type: str = "invalid_request_error",
) -> JSONResponse:
    return error_response(ApiError(status_code, error_type, code, message))


def parse_embedding_request(payload: Any, expected_model: str) -> EmbeddingRequest:
    if not isinstance(payload, dict):
        raise ApiError(
            400,
            "invalid_request_error",
            "invalid_request_body",
            "Request body must be a JSON object.",
        )

    allowed_keys = {"model", "input", "encoding_format", "user"}
    extra_keys = sorted(set(payload.keys()) - allowed_keys)
    if extra_keys:
        raise ApiError(
            400,
            "invalid_request_error",
            "unsupported_parameter",
            f"Unsupported parameter: {extra_keys[0]}.",
        )

    model = payload.get("model")
    if not isinstance(model, str) or not model:
        raise ApiError(
            400,
            "invalid_request_error",
            "missing_required_parameter",
            "Field 'model' is required and must be a non-empty string.",
        )
    if model != expected_model:
        raise ApiError(
            400,
            "invalid_request_error",
            "unsupported_model",
            f"Unsupported model '{model}'. Expected '{expected_model}'.",
        )

    raw_input = payload.get("input")
    if isinstance(raw_input, list):
        raise ApiError(
            400,
            "invalid_request_error",
            "array_input_not_allowed",
            "This SLA endpoint only accepts a single string input, not an array.",
        )
    if not isinstance(raw_input, str):
        raise ApiError(
            400,
            "invalid_request_error",
            "invalid_input_type",
            "Field 'input' must be a string.",
        )
    if raw_input == "":
        raise ApiError(
            400,
            "invalid_request_error",
            "empty_input",
            "Field 'input' must not be empty.",
        )

    encoding_format = payload.get("encoding_format", "float")
    if encoding_format is None:
        encoding_format = "float"
    if encoding_format != "float":
        raise ApiError(
            400,
            "invalid_request_error",
            "unsupported_encoding_format",
            "Only encoding_format='float' is supported by this baseline.",
        )

    return EmbeddingRequest(model=model, input=raw_input, encoding_format=encoding_format)
