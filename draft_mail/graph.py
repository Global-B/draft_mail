import base64
import json
import os
import httpx
import requests
from azure.identity import AuthorizationCodeCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.importance import Importance
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.message import Message
from msgraph.generated.models.recipient import Recipient
from typing import List, Any, Dict


class Graph:
    user_client: GraphServiceClient
    client_secret_credential: AuthorizationCodeCredential

    scopes = ["User.Read", "Mail.Read", "Mail.Send", "Mail.ReadWrite"]

    def __init__(self, code: str = None):
        client_id = os.getenv("CLIENT_ID")
        tenant_id = os.getenv("TENANT_ID")
        redirect_uri = os.getenv("REDIRECT_URI")

        self.client_secret_credential = AuthorizationCodeCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            authorization_code=code,
            redirect_uri=redirect_uri,
        )

        self.user_client = GraphServiceClient(
            credentials=self.client_secret_credential, scopes=self.scopes
        )

    async def send_draft_email(
        self,
        subject: str,
        body: str,
        send_to_email: str,
        copy_to_emails: List[str] = [],
    ) -> Message:
        message = Message(
            subject=subject,
            importance=Importance.Normal,
            body=ItemBody(
                content_type=BodyType.Html,
                content=body,
            ),
            to_recipients=[
                Recipient(
                    email_address=EmailAddress(
                        address=send_to_email,
                    ),
                ),
            ],
            cc_recipients=(
                [
                    Recipient(email_address=EmailAddress(address=email))
                    for email in copy_to_emails
                ]
                if copy_to_emails and len(copy_to_emails) > 0
                else []
            ),
        )

        return await self.user_client.me.messages.post(message)
    
    # create a function to attatch a remote file
    async def attach_remote_file(self, message_id: str, file_url: str, file_name: str):
        # Get the file
        response = requests.get(file_url)
        file_content = response.content
        file_size = len(file_content)
        encoded_file_content = base64.b64encode(file_content).decode("utf-8")
        
        # file_name = file_name.split("/")[-1] if "/" in file_name else file_name

        # Get the token
        token = self.client_secret_credential.get_token(*self.scopes)
        # https://learn.microsoft.com/en-us/graph/api/message-post-attachments?view=graph-rest-1.0&tabs=http#tabpanel_1_python
        if file_size < 3 * 1024 * 1024:  # 3MB
            data = {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": file_name,
                "contentBytes": encoded_file_content,
            }

            url = (
                f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments"
            )
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token.token}",
            }
            response = requests.post(url, headers=headers, data=json.dumps(data))

        else:
            # https://learn.microsoft.com/en-us/graph/api/attachment-createuploadsession?view=graph-rest-1.0&tabs=http
            chunk_size = 4 * 1024 * 1024  # 4MB
            chunks = [
                file_content[i : i + chunk_size]
                for i in range(0, len(file_content), chunk_size)
            ]

            data = {
                "AttachmentItem": {
                    "attachmentType": "file",
                    "name": file_name,
                    "size": file_size,
                }
            }

            url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments/createUploadSession"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token.token}",
            }
            response = requests.post(url, headers=headers, data=json.dumps(data))

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
        

    async def attach_local_file(self, message_id: str, file_path: str, file_name: str):
        file_size = os.path.getsize(file_path)

        with open(file_path, "rb") as file:
            file_content = file.read()

        encoded_file_content = base64.b64encode(file_content).decode("utf-8")

        file_name = file_name.split("/")[-1] if "/" in file_name else file_name

        # Get the token
        token = self.client_secret_credential.get_token(*self.scopes)
        # https://learn.microsoft.com/en-us/graph/api/message-post-attachments?view=graph-rest-1.0&tabs=http#tabpanel_1_python
        if file_size < 3 * 1024 * 1024:  # 3MB
            data = {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": file_name,
                "contentBytes": encoded_file_content,
            }

            url = (
                f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments"
            )
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token.token}",
            }
            response = requests.post(url, headers=headers, data=json.dumps(data))

        else:
            # https://learn.microsoft.com/en-us/graph/api/attachment-createuploadsession?view=graph-rest-1.0&tabs=http
            chunk_size = 4 * 1024 * 1024  # 4MB
            chunks = [
                file_content[i : i + chunk_size]
                for i in range(0, len(file_content), chunk_size)
            ]

            data = {
                "AttachmentItem": {
                    "attachmentType": "file",
                    "name": file_name,
                    "size": file_size,
                }
            }

            url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments/createUploadSession"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token.token}",
            }
            response = requests.post(url, headers=headers, data=json.dumps(data))

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

    @staticmethod
    def get_login_link(object_id: str) -> Dict[str, Any]:
        extra_context = {}
        scopes = "User.Read Mail.Read Mail.Send Mail.ReadWrite"
        client_id = os.getenv("CLIENT_ID")
        tenant_id = os.getenv('TENANT_ID')
        redirect_uri = os.getenv('REDIRECT_URI')
        auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&response_mode=query&scope={scopes}&state={object_id}"
        extra_context['ms_auth_link'] = auth_url
        
        return extra_context