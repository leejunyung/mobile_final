import os
import cv2
import pathlib
import requests
from datetime import datetime

class ChangeDetection:
    result_prev = []
    HOST = 'http://127.0.0.1:8000'
    username = 'admin'
    password = '12345'
    token = ''
    title = ''
    text = ''

    def __init__(self, names):
        self.result_prev = [0 for _ in range(len(names))]
        try:
            # JSON 방식으로 요청
            res = requests.post(
            self.HOST + '/api-token-auth/',
            json={'username': self.username, 'password': self.password}
            )
            res.raise_for_status()  # 오류 발생 시 예외 발생
            self.token = res.json().get('token', '')
            if not self.token:
                raise ValueError("Failed to retrieve token.")
            print(f"Authentication successful, token: {self.token}")
        except Exception as e:
            print(f"Error during authentication: {e}")
            raise


    def authenticate(self):
        """
        Authenticate with the API and store the token.
        """
        try:
            res = requests.post(
                f"{self.HOST}/api-token-auth/",
                json={'username': self.username, 'password': self.password}
            )
            res.raise_for_status()  # Raise an error for non-200 status codes
            self.token = res.json().get('token', '')
            if not self.token:
                raise Exception("Failed to retrieve token.")
            print(f"Authentication successful, token: {self.token}")
        except Exception as e:
            print(f"Error during authentication: {e}")
            raise

    def add(self, names, detected_current, save_dir, image):
        """
        Detect changes and trigger sending if there is a change.
        """
        self.title = ''
        self.text = ''
        change_flag = 0  # Change detection flag
        for i in range(len(self.result_prev)):
            if self.result_prev[i] == 0 and detected_current[i] == 1:
                change_flag = 1
                self.title = names[i]
                self.text += f"{names[i]}, "
        self.result_prev = detected_current[:]  # Update detected states
        if change_flag == 1:
            self.send(save_dir, image)

    def send(self, save_dir, image):
        """
        Send the detected data with the image to the server.
        """
        try:
            now = datetime.now()
            save_path = (
                pathlib.Path(os.getcwd()) / save_dir / 'detected' /
                f"{now.year}" / f"{now.month:02}" / f"{now.day:02}"
            )
            save_path.mkdir(parents=True, exist_ok=True)
            full_path = save_path / f"{now.hour:02}-{now.minute:02}-{now.second:02}-{now.microsecond}.jpg"

            # Resize image
            dst = cv2.resize(image, dsize=(320, 240), interpolation=cv2.INTER_AREA)
            cv2.imwrite(str(full_path), dst)

            # Add authentication headers
            headers = {
                'Authorization': f'JWT {self.token}',
                'Accept': 'application/json'
            }
            # POST data
            data = {
            'author': 1,
            'title': self.title,
            'text': self.text.strip(', '),  # 쉼표 제거
            'created_date': datetime.now().isoformat(),  # ISO 8601 형식으로 변환
            'published_date': datetime.now().isoformat()  # 동일한 형식
            }
            files = {'image': open(full_path, 'rb')}


            # Send POST request
            res = requests.post(
                f"{self.HOST}/api_root/Post/",
                data=data, files=files, headers=headers
            )
            res.raise_for_status()  # Ensure the request succeeded
            print(f"Data sent successfully: {res.status_code}")
        except Exception as e:
            print(f"Error during sending data: {e}")
