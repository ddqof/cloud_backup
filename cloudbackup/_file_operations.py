import datetime
import os
import pickle


class FileOperations:
    @staticmethod
    def check_token(path):
        """
        :return: token if it's not expired, else None
        """
        if os.path.exists(path):
            with open(path, "rb") as f:
                token_data = pickle.load(f)
                expire_time = token_data["expire_time"]
                if datetime.datetime.now() < expire_time:
                    return token_data["token"]
        return None
