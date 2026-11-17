"""Small, mockable client for a private/local ComfyUI server.

This module does not start ComfyUI, download models, or invoke a GPU by itself.
The caller must supply an API-format workflow and an already running server.
"""
from __future__ import annotations

import time
from typing import Any

import requests


class ComfyUIError(RuntimeError):
    """Raised when ComfyUI rejects, fails, or cannot finish a workflow."""


class ComfyUIClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8188",
        *,
        session=None,
        request_timeout: float = 120.0,
        poll_interval: float = 1.0,
    ):
        self.base_url = str(base_url).rstrip("/")
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError("A URL do ComfyUI precisa usar HTTP ou HTTPS.")
        self.session = session or requests.Session()
        self.request_timeout = float(request_timeout)
        self.poll_interval = max(0.0, float(poll_interval))

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.request_timeout)
        try:
            response = getattr(self.session, method)(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            raise ComfyUIError(
                f"Falha na comunicação com ComfyUI em {path}: {str(exc)[:500]}"
            ) from exc

    def upload_image(
        self,
        image_bytes: bytes,
        filename: str = "nexus-keyframe.png",
        *,
        subfolder: str = "nexus",
    ) -> dict[str, Any]:
        """Upload a keyframe through ComfyUI's /upload/image route."""
        if not isinstance(image_bytes, bytes) or not image_bytes:
            raise ComfyUIError("O keyframe enviado ao ComfyUI está vazio.")
        if not filename or "/" in filename or "\\" in filename:
            raise ComfyUIError("Nome de arquivo inválido para upload ComfyUI.")
        response = self._request(
            "post",
            "/upload/image",
            data={"type": "input", "subfolder": subfolder, "overwrite": "true"},
            files={"image": (filename, image_bytes, "image/png")},
        )
        try:
            payload = response.json()
        except (ValueError, AttributeError) as exc:
            raise ComfyUIError("ComfyUI retornou uma resposta inválida ao enviar a imagem.") from exc
        if not isinstance(payload, dict) or not payload.get("name"):
            raise ComfyUIError("ComfyUI não confirmou o nome do arquivo enviado.")
        return payload

    def queue_prompt(self, workflow: dict[str, Any], *, client_id: str | None = None) -> str:
        """Submit a ComfyUI API-format workflow and return its prompt_id."""
        if not isinstance(workflow, dict) or not workflow:
            raise ComfyUIError("O workflow API do ComfyUI está vazio ou inválido.")
        body: dict[str, Any] = {"prompt": workflow}
        if client_id:
            body["client_id"] = str(client_id)
        response = self._request("post", "/prompt", json=body)
        try:
            payload = response.json()
        except (ValueError, AttributeError) as exc:
            raise ComfyUIError("ComfyUI retornou uma resposta inválida ao enfileirar o workflow.") from exc
        if not isinstance(payload, dict):
            raise ComfyUIError("ComfyUI retornou um contrato inválido ao enfileirar o workflow.")
        if payload.get("error") or payload.get("node_errors"):
            raise ComfyUIError(
                "ComfyUI rejeitou o workflow: "
                + str(payload.get("error") or payload.get("node_errors"))[:1200]
            )
        prompt_id = str(payload.get("prompt_id") or "").strip()
        if not prompt_id:
            raise ComfyUIError("ComfyUI não retornou prompt_id; o workflow não será reenviado automaticamente.")
        return prompt_id

    def get_history(self, prompt_id: str) -> dict[str, Any] | None:
        if not str(prompt_id).strip():
            raise ComfyUIError("prompt_id vazio ao consultar o histórico ComfyUI.")
        response = self._request("get", f"/history/{prompt_id}")
        try:
            payload = response.json()
        except (ValueError, AttributeError) as exc:
            raise ComfyUIError("ComfyUI retornou um histórico inválido.") from exc
        if not isinstance(payload, dict):
            raise ComfyUIError("ComfyUI retornou um histórico fora do formato esperado.")
        record = payload.get(prompt_id, payload)
        return record if isinstance(record, dict) and record else None

    @staticmethod
    def _execution_error(record: dict[str, Any]) -> str:
        status = record.get("status") or {}
        if isinstance(status, dict):
            status_text = str(status.get("status_str") or "").lower()
            if status_text in {"error", "failed", "failure"}:
                return status_text
            for message in status.get("messages", []) or []:
                if isinstance(message, (list, tuple)) and message:
                    if str(message[0]).lower() in {"execution_error", "execution_interrupted"}:
                        return str(message[1] if len(message) > 1 else message[0])[:1200]
        return ""

    def wait_for_prompt(
        self,
        prompt_id: str,
        *,
        timeout_seconds: float = 900.0,
        poll_interval: float | None = None,
    ) -> dict[str, Any]:
        """Poll history without resubmitting or retrying an expensive workflow."""
        deadline = time.monotonic() + max(0.0, float(timeout_seconds))
        interval = self.poll_interval if poll_interval is None else max(0.0, float(poll_interval))
        while True:
            record = self.get_history(prompt_id)
            if record is not None:
                failure = self._execution_error(record)
                if failure:
                    raise ComfyUIError(f"ComfyUI falhou ao executar {prompt_id}: {failure}")
                status = record.get("status") or {}
                status_text = str(status.get("status_str") or "").lower() if isinstance(status, dict) else ""
                if isinstance(status, dict) and (
                    status.get("completed") is True or status_text in {"success", "completed"}
                ):
                    return record
            if time.monotonic() >= deadline:
                raise ComfyUIError(
                    f"Tempo limite aguardando o workflow ComfyUI {prompt_id}. "
                    "O cliente não reenviou o trabalho automaticamente."
                )
            time.sleep(interval)

    @staticmethod
    def find_video_output(history: dict[str, Any]) -> dict[str, str]:
        """Find the first saved video reference in a ComfyUI history record."""
        outputs = history.get("outputs") or {}
        if not isinstance(outputs, dict):
            raise ComfyUIError("O histórico ComfyUI não contém outputs válidos.")
        for node_output in outputs.values():
            if not isinstance(node_output, dict):
                continue
            for field in ("videos", "gifs", "files"):
                entries = node_output.get(field) or []
                if not isinstance(entries, list):
                    continue
                for entry in entries:
                    if not isinstance(entry, dict) or not entry.get("filename"):
                        continue
                    filename = str(entry["filename"])
                    if filename.lower().endswith((".mp4", ".webm", ".mov", ".mkv")):
                        return {
                            "filename": filename,
                            "subfolder": str(entry.get("subfolder") or ""),
                            "type": str(entry.get("type") or "output"),
                        }
        raise ComfyUIError("O workflow terminou, mas não salvou um arquivo de vídeo reconhecível.")

    def download_output(self, file_reference: dict[str, str]) -> bytes:
        filename = str(file_reference.get("filename") or "").strip()
        if not filename:
            raise ComfyUIError("Referência de saída sem filename.")
        response = self._request(
            "get",
            "/view",
            params={
                "filename": filename,
                "subfolder": str(file_reference.get("subfolder") or ""),
                "type": str(file_reference.get("type") or "output"),
            },
        )
        content = getattr(response, "content", b"")
        if not isinstance(content, bytes) or not content:
            raise ComfyUIError("ComfyUI retornou um arquivo de saída vazio.")
        return content
