"""Submit Remotion render jobs to the dedicated GitHub Actions worker."""
import io
import json
import time
import uuid
import zipfile

import requests

from nexus.render_crypto import decrypt_bytes, decrypt_text, encrypt_text


API = "https://api.github.com"
DEFAULT_REPOSITORY = "porraloca42-stack/nexus-video-studio-"
WORKFLOW = "nexus-render-worker.yml"


class GitHubRenderError(RuntimeError):
    pass


def render_on_github(
    plan,
    voice,
    token,
    *,
    encryption_secret=None,
    repository=DEFAULT_REPOSITORY,
    timeout=2400,
    poll_interval=8,
    progress_callback=None,
    session=None,
):
    if not token:
        raise GitHubRenderError("Configure GITHUB_ACTIONS_TOKEN nos Secrets do Streamlit.")
    if not encryption_secret:
        raise GitHubRenderError("Configure CLOUDFLARE_API_TOKEN nos Secrets do Streamlit para proteger o conteúdo do render.")
    if not isinstance(plan, dict) or not plan.get("scenes"):
        raise ValueError("O storyboard não contém cenas.")
    manifest_json = json.dumps(plan, ensure_ascii=False, separators=(",", ":"))
    if len(manifest_json) > 45000:
        raise GitHubRenderError("O storyboard excede o limite seguro de envio ao GitHub Actions.")

    client = session or requests
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    job_id = f"nexus-{uuid.uuid4().hex[:12]}"
    workflow_url = f"{API}/repos/{repository}/actions/workflows/{WORKFLOW}/dispatches"
    dispatch = client.post(
        workflow_url,
        headers=headers,
        json={
            "ref": "main",
            "inputs": {
                "job_id": job_id,
                "manifest_encrypted": encrypt_text(manifest_json, encryption_secret),
                "voice": voice,
            },
        },
        timeout=30,
    )
    if dispatch.status_code not in (201, 204):
        raise GitHubRenderError(
            f"GitHub recusou o trabalho (HTTP {dispatch.status_code}): {dispatch.text[:1200]}"
        )

    expected_name = f"NEXUS render {job_id}"
    runs_url = f"{API}/repos/{repository}/actions/runs"
    started = time.monotonic()
    run = None
    while time.monotonic() - started < timeout:
        response = client.get(
            runs_url,
            headers=headers,
            params={"event": "workflow_dispatch", "branch": "main", "per_page": 100},
            timeout=30,
        )
        if response.status_code != 200:
            raise GitHubRenderError(
                f"Não foi possível consultar o trabalho no GitHub (HTTP {response.status_code})."
            )
        runs = response.json().get("workflow_runs", [])
        run = next(
            (
                item for item in runs
                if item.get("name") == expected_name or item.get("display_title") == expected_name
            ),
            None,
        )
        if run:
            break
        if progress_callback:
            progress_callback("Aguardando o GitHub iniciar o renderizador...")
        time.sleep(poll_interval)

    if not run:
        raise GitHubRenderError("O GitHub não iniciou o trabalho dentro do tempo esperado.")

    run_id = run["id"]
    while time.monotonic() - started < timeout:
        response = client.get(
            f"{API}/repos/{repository}/actions/runs/{run_id}",
            headers=headers,
            timeout=30,
        )
        if response.status_code != 200:
            raise GitHubRenderError(f"Não foi possível consultar o render (HTTP {response.status_code}).")
        run = response.json()
        status = run.get("status")
        if progress_callback:
            progress_callback(
                "Renderização Remotion em andamento..." if status != "completed"
                else "Renderização concluída; recuperando o MP4..."
            )
        if status == "completed":
            break
        time.sleep(poll_interval)
    else:
        raise GitHubRenderError("O render excedeu o tempo máximo de espera.")

    if run.get("conclusion") != "success":
        raise GitHubRenderError(
            f"O render no GitHub terminou com status: {run.get('conclusion') or 'desconhecido'}. "
            f"Consulte a execução {run_id} no GitHub Actions."
        )

    artifacts_response = client.get(
        f"{API}/repos/{repository}/actions/runs/{run_id}/artifacts",
        headers=headers,
        timeout=30,
    )
    if artifacts_response.status_code != 200:
        raise GitHubRenderError("Não foi possível localizar o artefato MP4 do render.")
    artifact_name = f"nexus-render-{job_id}"
    artifact = next(
        (item for item in artifacts_response.json().get("artifacts", []) if item.get("name") == artifact_name),
        None,
    )
    if not artifact:
        raise GitHubRenderError("O trabalho terminou, mas o artefato MP4 não foi publicado.")

    archive = client.get(
        f"{API}/repos/{repository}/actions/artifacts/{artifact['id']}/zip",
        headers=headers,
        timeout=120,
    )
    if archive.status_code != 200:
        raise GitHubRenderError(f"Não foi possível baixar o MP4 (HTTP {archive.status_code}).")

    with zipfile.ZipFile(io.BytesIO(archive.content)) as bundle:
        mp4_name = next((name for name in bundle.namelist() if name.endswith("nexus_video.mp4.enc")), None)
        report_name = next((name for name in bundle.namelist() if name.endswith("render-report.json.enc")), None)
        if not mp4_name:
            raise GitHubRenderError("O artefato não contém o MP4 criptografado esperado.")
        video_bytes = decrypt_bytes(bundle.read(mp4_name), encryption_secret)
        report = json.loads(decrypt_text(bundle.read(report_name).decode("ascii"), encryption_secret)) if report_name else {}
    if not video_bytes:
        raise GitHubRenderError("O MP4 recuperado está vazio.")
    return {"video": video_bytes, "report": report, "run_id": run_id, "job_id": job_id}
