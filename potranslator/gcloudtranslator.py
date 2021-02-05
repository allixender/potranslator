import google.auth
from google.cloud import translate
import os
import toolz
from operator import add
from functools import reduce


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

    def count_chars(self, trans_text):
        """
        text should only be a list[list[str]]
        """
        mins = 5000
        maxs = 30000
        steps = 1
        cutoffs = []
        for r in enumerate(toolz.accumulate(add, toolz.map(len, trans_text))):
            if r[1] >= mins * steps and r[1] < maxs * steps:
                cutoffs.append(r[0])
                steps = steps + 1
            elif r[1] >= mins * steps and r[1] >= maxs * steps:
                if steps > 1:
                    cutoffs.append(r[0] - 1)
                    steps = steps + 1
                else:
                    cutoffs.append(r[0])
                    print(f"single string element too long!  (l: {r[1]})")
        cutoffs.append(len(trans_text))
        print(
            f"make_batch for {sum(list(map(len, trans_text)))} chars in {len(trans_text)} seqs | calculated cutoffs: {cutoffs}"
        )
        return cutoffs

    def make_batches(self, trans_text, src, dest, parent):
        """
        The Cloud Translation API is optimized for a recommended length for each request of 5K characters (code points).
        For Cloud Translation - Advanced, the maximum number of code points for a single request is 30K.
        """
        template_request = {
            "parent": parent,
            "contents": [],
            "mime_type": "text/plain",  # mime types: text/plain, text/html
            "target_language_code": dest,
        }
        if not src == "auto":
            template_request.update({"source_language_code": src})

        cuts = self.count_chars(trans_text)

        request_batches = []

        if len(cuts) < 1:
            tr = template_request.copy()
            tr["contents"] = trans_text
            request_batches.append(tr)
        else:
            x = toolz.first(cuts)
            rest = list(toolz.drop(1, cuts))

            for et in enumerate(trans_text):
                if x < et[0]:
                    tr = template_request.copy()
                    tr["contents"].append(et[1])
                    request_batches.append(tr)
                else:
                    cuts = rest
                    if len(cuts) > 0:
                        x = toolz.first(cuts)
                        rest = list(toolz.drop(1, cuts))

        return request_batches

    def translate(self, trans_text, src="auto", dest="en"):

        # Detail on supported types can be found here
        location = "global"
        parent = f"projects/{self.project}/locations/{location}"

        # https://cloud.google.com/translate/docs/supported-formats
        send_list = trans_text
        if isinstance(trans_text, str):
            send_list = [translate]

        request_preps = self.make_batches(send_list, src, dest, parent)

        responses = toolz.map(
            lambda req: self.tclient.translate_text(request=req), request_preps
        )

        result = []
        for response in responses:
            # Display the translation for each input text provided
            for translation in response.translations:
                # print("Translated text: {}".format(translation.translated_text))
                result.append(TranslatedText(translation, src, dest))

        return result
