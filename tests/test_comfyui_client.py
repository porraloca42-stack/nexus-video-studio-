import unittest
from unittest.mock import Mock, patch

from nexus.comfyui_client import ComfyUIClient, ComfyUIError, patch_api_workflow, validate_api_workflow


class FakeResponse:
    def __init__(self, payload=None, content=b""):
        self.payload = payload if payload is not None else {}
        self.content = content

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.calls = []

    def _next(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if not self.responses:
            raise AssertionError("Unexpected HTTP request")
        return self.responses.pop(0)

    def post(self, url, **kwargs):
        return self._next("post", url, **kwargs)

    def get(self, url, **kwargs):
        return self._next("get", url, **kwargs)


class ComfyUIAPIWorkflowValidationTests(unittest.TestCase):
    def test_accepts_well_formed_api_graph_and_links(self):
        workflow = {
            "1": {"class_type": "LoadImage", "inputs": {"image": "keyframe.png"}},
            "2": {"class_type": "SaveVideo", "inputs": {"images": ["1", 0]}},
        }
        self.assertTrue(validate_api_workflow(workflow))

    def test_rejects_missing_class_type_or_inputs(self):
        with self.assertRaisesRegex(ComfyUIError, "class_type"):
            validate_api_workflow({"1": {"inputs": {}}})
        with self.assertRaisesRegex(ComfyUIError, "inputs"):
            validate_api_workflow({"1": {"class_type": "SaveVideo"}})

    def test_rejects_dangling_node_references(self):
        workflow = {
            "2": {"class_type": "SaveVideo", "inputs": {"images": ["99", 0]}},
        }
        with self.assertRaisesRegex(ComfyUIError, "referencia nó ausente 99"):
            validate_api_workflow(workflow)

    def test_rejects_malformed_or_negative_output_slots(self):
        for link in (["1"], ["1", -1], ["1", True], ["1", "0"]):
            workflow = {
                "1": {"class_type": "LoadImage", "inputs": {}},
                "2": {"class_type": "SaveVideo", "inputs": {"images": link}},
            }
            with self.subTest(link=link), self.assertRaisesRegex(ComfyUIError, "Conexão inválida"):
                validate_api_workflow(workflow)


class ComfyUIClientTests(unittest.TestCase):
    def test_upload_image_uses_local_input_upload_contract(self):
        session = FakeSession([FakeResponse({"name": "nexus/keyframe.png", "type": "input"})])
        client = ComfyUIClient(session=session)

        result = client.upload_image(b"png-bytes", "keyframe.png")

        self.assertEqual(result["name"], "nexus/keyframe.png")
        method, url, kwargs = session.calls[0]
        self.assertEqual((method, url), ("post", "http://127.0.0.1:8188/upload/image"))
        self.assertEqual(kwargs["data"]["type"], "input")
        self.assertEqual(kwargs["files"]["image"][1], b"png-bytes")

    def test_upload_rejects_empty_image_before_network(self):
        session = FakeSession()
        client = ComfyUIClient(session=session)

        with self.assertRaises(ComfyUIError):
            client.upload_image(b"")

        self.assertEqual(session.calls, [])

    def test_patch_api_workflow_changes_only_explicit_widget_inputs(self):
        workflow = {
            "10": {
                "class_type": "LoadImage",
                "inputs": {"image": "old.png", "upload": "image"},
            },
            "20": {
                "class_type": "PrimitiveInt",
                "inputs": {"value": 121},
            },
        }

        patched = patch_api_workflow(workflow, {
            "keyframe": {"node_id": "10", "input_name": "image", "value": "new.png"},
            "frame_count": {"node_id": "20", "input_name": "value", "value": 73},
        })

        self.assertEqual(patched["10"]["inputs"]["image"], "new.png")
        self.assertEqual(patched["20"]["inputs"]["value"], 73)
        self.assertEqual(workflow["10"]["inputs"]["image"], "old.png")
        self.assertEqual(workflow["20"]["inputs"]["value"], 121)

    def test_patch_api_workflow_wraps_array_widget_values(self):
        workflow = {
            "10": {
                "class_type": "PrimitiveArray",
                "inputs": {"value": [1, 2, 3]},
            }
        }

        patched = patch_api_workflow(workflow, {
            "curve": {"node_id": "10", "input_name": "value", "value": [4, 5, 6]},
        })

        self.assertEqual(patched["10"]["inputs"]["value"], {"__value__": [4, 5, 6]})
        self.assertEqual(workflow["10"]["inputs"]["value"], [1, 2, 3])
        self.assertTrue(validate_api_workflow(patched))

    def test_patch_api_workflow_rejects_linked_inputs(self):
        workflow = {
            "10": {
                "class_type": "LTXVPreprocess",
                "inputs": {"image": ["4", 0]},
            }
        }

        with self.assertRaisesRegex(ComfyUIError, "está conectado"):
            patch_api_workflow(workflow, {
                "keyframe": {"node_id": "10", "input_name": "image", "value": "new.png"},
            })

    def test_patch_api_workflow_rejects_unknown_node_or_input(self):
        with self.assertRaisesRegex(ComfyUIError, "ausente"):
            patch_api_workflow(
                {"10": {"class_type": "LoadImage", "inputs": {"image": "old.png"}}},
                {"keyframe": {"node_id": "99", "input_name": "image", "value": "new.png"}},
            )

    def test_queue_prompt_returns_prompt_id_and_sends_api_workflow(self):
        session = FakeSession([FakeResponse({"prompt_id": "job-123", "number": 1})])
        client = ComfyUIClient(session=session)
        workflow = {"10": {"class_type": "SaveVideo", "inputs": {}}}

        prompt_id = client.queue_prompt(workflow, client_id="nexus-test")

        self.assertEqual(prompt_id, "job-123")
        self.assertEqual(session.calls[0][2]["json"], {
            "prompt": workflow,
            "client_id": "nexus-test",
        })

    def test_queue_prompt_rejects_malformed_api_graph_before_network(self):
        session = FakeSession()
        client = ComfyUIClient(session=session)

        with self.assertRaisesRegex(ComfyUIError, "referencia nó ausente"):
            client.queue_prompt({
                "20": {"class_type": "SaveVideo", "inputs": {"images": ["99", 0]}},
            })

        self.assertEqual(session.calls, [])

    def test_queue_prompt_rejects_node_errors_without_retry(self):
        session = FakeSession([FakeResponse({"error": "invalid prompt", "node_errors": {"10": "bad"}})])
        client = ComfyUIClient(session=session)

        with self.assertRaisesRegex(ComfyUIError, "rejeitou o workflow"):
            client.queue_prompt({"10": {"class_type": "SaveVideo", "inputs": {}}})

        self.assertEqual(len(session.calls), 1)

    def test_wait_for_prompt_returns_only_after_success_status(self):
        client = ComfyUIClient(session=FakeSession(), poll_interval=0)
        client.get_history = Mock(return_value={
            "status": {"status_str": "success", "completed": True},
            "outputs": {"20": {"videos": [{"filename": "scene.mp4"}]}},
        })

        result = client.wait_for_prompt("job-123", timeout_seconds=1)

        self.assertEqual(result["status"]["status_str"], "success")
        client.get_history.assert_called_once_with("job-123")

    def test_wait_for_prompt_raises_on_execution_error(self):
        client = ComfyUIClient(session=FakeSession(), poll_interval=0)
        client.get_history = Mock(return_value={
            "status": {
                "status_str": "error",
                "completed": True,
                "messages": [["execution_error", {"exception_message": "out of memory"}]],
            }
        })

        with self.assertRaisesRegex(ComfyUIError, "falhou ao executar"):
            client.wait_for_prompt("job-123", timeout_seconds=1)

    def test_wait_for_prompt_times_out_without_resubmitting(self):
        client = ComfyUIClient(session=FakeSession(), poll_interval=0)
        client.get_history = Mock(return_value=None)

        with patch("nexus.comfyui_client.time.monotonic", side_effect=[0.0, 2.0]):
            with self.assertRaisesRegex(ComfyUIError, "não reenviou"):
                client.wait_for_prompt("job-123", timeout_seconds=1)

        client.get_history.assert_called_once_with("job-123")

    def test_find_video_output_and_download_output(self):
        history = {
            "outputs": {
                "55": {
                    "videos": [{
                        "filename": "nexus/scene.mp4",
                        "subfolder": "nexus",
                        "type": "output",
                    }]
                }
            }
        }
        reference = ComfyUIClient.find_video_output(history)
        session = FakeSession([FakeResponse(content=b"mp4-data")])
        client = ComfyUIClient(session=session)

        content = client.download_output(reference)

        self.assertEqual(content, b"mp4-data")
        self.assertEqual(session.calls[0][2]["params"], {
            "filename": "nexus/scene.mp4",
            "subfolder": "nexus",
            "type": "output",
        })

    def test_find_video_output_rejects_missing_video(self):
        with self.assertRaisesRegex(ComfyUIError, "não salvou"):
            ComfyUIClient.find_video_output({"outputs": {"1": {"images": [{"filename": "frame.png"}]}}})

    def test_base_url_must_be_http_or_https(self):
        with self.assertRaises(ValueError):
            ComfyUIClient("ftp://127.0.0.1:8188")


if __name__ == "__main__":
    unittest.main()
