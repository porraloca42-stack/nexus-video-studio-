import unittest

from nexus.render_crypto import decrypt_bytes, decrypt_text, decrypt_compressed_text, encrypt_bytes, encrypt_text, encrypt_compressed_text


class RenderCryptoTests(unittest.TestCase):
    def test_text_round_trip(self):
        secret = "test-cloudflare-token"
        encrypted = encrypt_text('{"title":"roteiro privado"}', secret)
        self.assertNotIn("roteiro privado", encrypted)
        self.assertEqual(decrypt_text(encrypted, secret), '{"title":"roteiro privado"}')

    def test_compressed_text_round_trip(self):
        secret = "test-cloudflare-token"
        payload = '{"scenes":[' + ','.join(
            '{"image_prompt":"cinematic visual direction with repeated descriptive detail"}'
            for _ in range(20)
        ) + ']}'
        encrypted = encrypt_compressed_text(payload, secret)
        self.assertLess(len(encrypted), len(payload))
        self.assertEqual(decrypt_compressed_text(encrypted, secret), payload)

    def test_binary_round_trip(self):
        secret = "test-cloudflare-token"
        payload = b"\x00private-mp4-bytes\xff"
        encrypted = encrypt_bytes(payload, secret)
        self.assertNotIn(payload, encrypted)
        self.assertEqual(decrypt_bytes(encrypted, secret), payload)

    def test_wrong_secret_is_rejected(self):
        encrypted = encrypt_text("private", "first-token")
        with self.assertRaises(ValueError):
            decrypt_text(encrypted, "different-token")


if __name__ == "__main__":
    unittest.main()
