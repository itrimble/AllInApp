import unittest
from unittest.mock import patch, MagicMock
import os
from AllInApp.tts import generate_tts
# It's good practice to import gTTS if we need to check for specific gTTS exceptions,
# but for this test, we're mostly mocking its behavior.
# from gtts import gTTS # Uncomment if needed for specific exception types from gTTS

class TestTTS(unittest.TestCase):

    def setUp(self):
        # Create a dummy output directory for tests if needed, though mocking should prevent file creation.
        self.test_output_dir = "test_tts_output_dir"
        if not os.path.exists(self.test_output_dir):
            os.makedirs(self.test_output_dir)
        self.sample_text = "Hello world"
        self.output_path = os.path.join(self.test_output_dir, "test_output.mp3")

    def tearDown(self):
        # Clean up the dummy directory and any files if created.
        if os.path.exists(self.output_path):
            os.remove(self.output_path)
        if os.path.exists(self.test_output_dir):
            os.rmdir(self.test_output_dir)

    @patch('AllInApp.tts.gTTS')
    def test_generate_tts_success(self, mock_gtts_class):
        """Test successful TTS generation."""
        mock_gtts_instance = MagicMock()
        mock_gtts_class.return_value = mock_gtts_instance

        generate_tts(self.sample_text, self.output_path, language='en')

        mock_gtts_class.assert_called_once_with(text=self.sample_text, lang='en', slow=False)
        mock_gtts_instance.save.assert_called_once_with(self.output_path)
        # Assuming generate_tts prints success and doesn't return a specific value for success.
        # If it were to return True on success, we'd assert that:
        # self.assertTrue(result)

    @patch('AllInApp.tts.gTTS')
    @patch('builtins.print')
    def test_generate_tts_file_saving_error(self, mock_print, mock_gtts_class):
        """Test TTS generation when gTTS.save() raises an IOError."""
        mock_gtts_instance = MagicMock()
        mock_gtts_class.return_value = mock_gtts_instance
        mock_gtts_instance.save.side_effect = IOError("Permission denied")

        generate_tts(self.sample_text, self.output_path)

        mock_gtts_class.assert_called_once_with(text=self.sample_text, lang='en', slow=False)
        mock_gtts_instance.save.assert_called_once_with(self.output_path)

        # Check that an error message was printed
        error_message_found = False
        for call_args in mock_print.call_args_list:
            if "An error occurred: Permission denied" in call_args[0][0]:
                error_message_found = True
                break
        self.assertTrue(error_message_found, "Error message about file saving was not printed.")
        # Assuming the function currently prints an error and doesn't return True/False or raise.
        # If it were to return False, self.assertFalse(result)

    @patch('AllInApp.tts.gTTS')
    @patch('builtins.print')
    def test_generate_tts_gtts_error_general(self, mock_print, mock_gtts_class):
        """Test TTS generation when gTTS itself raises an error during initialization."""
        # This could simulate various gTTS internal errors, including some invalid lang issues
        # if they manifest as exceptions from the gTTS constructor.
        mock_gtts_class.side_effect = Exception("gTTS initialization failed")

        generate_tts(self.sample_text, self.output_path, language='invalid_lang')

        mock_gtts_class.assert_called_once_with(text=self.sample_text, lang='invalid_lang', slow=False)

        error_message_found = False
        for call_args in mock_print.call_args_list:
            if "An error occurred: gTTS initialization failed" in call_args[0][0]:
                error_message_found = True
                break
        self.assertTrue(error_message_found, "Error message about gTTS initialization was not printed.")

    # Note on testing invalid language specifically:
    # gTTS might handle invalid language codes by falling back to a default or raising
    # a specific exception (e.g., related to network if it fetches language data,
    # or a ValueError if it's a predefined list).
    # If gTTS raises a *specific* exception for invalid language that `generate_tts`
    # is expected to catch differently, a more targeted test would be needed.
    # However, the `test_generate_tts_gtts_error_general` covers general exceptions
    # from gTTS constructor, which might include language issues.
    # Without knowing the exact behavior of gTTS for invalid languages (which can also change
    # between gTTS versions), a general exception handling test is a good start.

if __name__ == '__main__':
    unittest.main()
