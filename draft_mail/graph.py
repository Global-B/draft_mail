import base64
import json
import os
import httpx
import requests
from azure.identity import AuthorizationCodeCredential
from azure.core.credentials import AccessToken
from msgraph import GraphServiceClient
from typing import List, Any, Dict, Optional
from urllib.parse import urlencode


class Graph:
    user_client: GraphServiceClient
    client_secret_credential: AuthorizationCodeCredential
    current_access_token: Optional[AccessToken]
    default_url: str = "https://graph.microsoft.com/v1.0/me/messages"

    scopes = ["User.Read", "Mail.Read", "Mail.Send", "Mail.ReadWrite"]

    def __init__(self, code: str = None, default_url: Optional[str] = None):
        client_id = os.getenv("CLIENT_ID")
        tenant_id = os.getenv("TENANT_ID")
        redirect_uri = os.getenv("REDIRECT_URI")

        if default_url:
            self.default_url = default_url

        self.client_secret_credential = AuthorizationCodeCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            authorization_code=code,
            redirect_uri=redirect_uri,
        )

        self.user_client = GraphServiceClient(
            credentials=self.client_secret_credential, scopes=self.scopes
        )

        self._ensure_token()

    def _ensure_token(self) -> AccessToken | None:
        try:
            # This will either use the cached token or acquire a new one
            token = self.client_secret_credential.get_token(*self.scopes)
            self.current_access_token = token
            return token
        except Exception:
            # If token acquisition fails, you might need to re-authenticate
            print("Authentication failed. You may need to re-authenticate.")
            # Here you could implement logic to get a new authorization code
            return None

    async def send_draft_email(
            self, subject: str, body: str, send_to_email: str, copy_to_emails: List[str] = []
    ) -> Dict[str, Any]:

        if not self.current_access_token:
            raise Exception("No se ha podido obtener el token")

        headers = {
            "Authorization": f"Bearer {self.current_access_token.token}",
            "Content-Type": "application/json"
        }

        email_data = {
            "subject": subject,
            "importance": "Low",
            "body": {
                "contentType": "HTML",
                "content": body
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": send_to_email
                    }
                }
            ],
            "ccRecipients": [
                {
                    "emailAddress": {
                        "address": email
                    }
                } for email in copy_to_emails
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.default_url, headers=headers, json=email_data)
            if response.status_code == 201:
                return response.json()
            else:
                error_text = response.content
                raise Exception(
                    f"Failed to send draft email. Status: {response.status_code}, Error: {error_text}")

    async def attach_local_file(self, message_id: str, file_path: str, file_name: str):
        file_size = os.path.getsize(file_path)

        with open(file_path, "rb") as file:
            file_content = file.read()

        encoded_file_content = base64.b64encode(file_content).decode("utf-8")

        file_name = file_name.split("/")[-1] if "/" in file_name else file_name

        # Get the token
        token = self.current_access_token
        # https://learn.microsoft.com/en-us/graph/api/message-post-attachments?view=graph-rest-1.0&tabs=http#tabpanel_1_python
        if file_size < 3 * 1024 * 1024:  # 3MB
            data = {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": file_name,
                "contentBytes": encoded_file_content,
            }

            url = (
                f"{self.default_url}/{message_id}/attachments"
            )
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token.token}",
            }
            response = requests.post(
                url, headers=headers, data=json.dumps(data))

        else:
            # https://learn.microsoft.com/en-us/graph/api/attachment-createuploadsession?view=graph-rest-1.0&tabs=http
            chunk_size = 4 * 1024 * 1024  # 4MB
            chunks = [
                file_content[i: i + chunk_size]
                for i in range(0, len(file_content), chunk_size)
            ]

            data = {
                "AttachmentItem": {
                    "attachmentType": "file",
                    "name": file_name,
                    "size": file_size,
                }
            }

            url = f"{self.default_url}/{message_id}/attachments/createUploadSession"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token.token}",
            }
            response = requests.post(
                url, headers=headers, data=json.dumps(data))

            update_url = response.json().get("uploadUrl")
            async with httpx.AsyncClient() as client:
                for i, chunk in enumerate(chunks):
                    start = i * chunk_size
                    end = (
                        start + len(chunk) - 1
                    )  # Calculate the end based on the actual size of the chunk
                    headers = {
                        "Content-Length": str(len(chunk)),
                        "Content-Type": "application/octet-stream",
                        "Content-Range": f"bytes {start}-{end}/{file_size}",
                    }
                    await client.put(update_url, headers=headers, content=chunk)

        return response

    async def attach_bytes(self, message_id: str, file_bytes: bytes, file_name: str):
        # Get the token
        token = self.current_access_token
        # https://learn.microsoft.com/en-us/graph/api/message-post-attachments?view=graph-rest-1.0&tabs=http#tabpanel_1_python
        if len(file_bytes) < 3 * 1024 * 1024:  # 3MB
            data = {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": file_name,
                "contentBytes": base64.b64encode(file_bytes).decode("utf-8"),
            }
            url = (
                f"{self.default_url}/{message_id}/attachments"
            )
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token.token}",
            }
            response = requests.post(
                url, headers=headers, data=json.dumps(data))
        else:
            # https://learn.microsoft.com/en-us/graph/api/attachment-createuploadsession?view=graph-rest-1.0&tabs=http
            chunk_size = 4 * 1024 * 1024  # 4MB
            chunks = [
                file_bytes[i: i + chunk_size]
                for i in range(0, len(file_bytes), chunk_size)
            ]
            data = {
                "AttachmentItem": {
                    "attachmentType": "file",
                    "name": file_name,
                    "size": len(file_bytes),
                }
            }
            url = f"{self.default_url}/{message_id}/attachments/createUploadSession"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token.token}",
            }
            response = requests.post(
                url, headers=headers, data=json.dumps(data))
            update_url = response.json().get("uploadUrl")
            async with httpx.AsyncClient() as client:
                for i, chunk in enumerate(chunks):
                    start = i * chunk_size
                    end = (
                        start + len(chunk) - 1
                    )  # Calculate the end based on the actual size of the chunk
                    headers = {
                        "Content-Length": str(len(chunk)),
                        "Content-Type": "application/octet-stream",
                        "Content-Range": f"bytes {start}-{end}/{len(file_bytes)}",
                    }
                    await client.put(update_url, headers=headers, content=chunk)
        return response

    async def attach_remote_file(self, message_id: str, file_url: str, file_name: str):
        # Get the file
        response = requests.get(file_url)
        file_content = response.content

        response = await self.attach_bytes(message_id, file_content, file_name)

        return response

    @staticmethod
    def get_login_link(object_id: str) -> Dict[str, Any]:
        extra_context = {}
        scopes = "User.Read Mail.Read Mail.Send Mail.ReadWrite"
        client_id = os.getenv("CLIENT_ID")
        tenant_id = os.getenv('TENANT_ID')
        redirect_uri = os.getenv('REDIRECT_URI')

        base_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"

        # Create a dictionary of query parameters
        query_params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "response_mode": "query",
            "scope": scopes,
            "state": object_id
        }

        # Construct the full URL
        auth_url = f"{base_url}?{urlencode(query_params)}"

        # Add to extra_context
        extra_context['ms_auth_link'] = auth_url
        

        return extra_context
