import google.auth
from google.cloud import translate
import os


class TranslatedText(object):
    def __init__(self, google_translation, src, dest):
        self.text = google_translation.translated_text
        self.src = src
        self.dest = dest


class Translator(object):
    def __init__(self):
        if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "") == "":
            raise ValueError(
                "Please set GOOGLE_APPLICATION_CREDENTIALS service account json"
            )
        else:
            self.credentials, self.project = google.auth.default()
            self.tclient = translate.TranslationServiceClient()

    def translate(self, trans_text, src="auto", dest="en"):
        location = "global"
        parent = f"projects/{self.project}/locations/{location}"

        # Detail on supported types can be found here:
        # https://cloud.google.com/translate/docs/supported-formats
        send_list = trans_text
        if isinstance(trans_text, str):
            send_list = [translate]

        trequest = {
            "parent": parent,
            "contents": send_list,
            "mime_type": "text/plain",  # mime types: text/plain, text/html
            "target_language_code": dest,
        }

        if not src == "auto":
            trequest.update({"source_language_code": src})

        response = self.tclient.translate_text(request=trequest)
        result = []
        # Display the translation for each input text provided
        for translation in response.translations:
            # print("Translated text: {}".format(translation.translated_text))
            result.append(TranslatedText(translation, src, dest))

        return result
