# django_insurance_draft_mail

A Django package that provides a graph api to send draft emails

## Installation

Install the package using pip:

```bash
pip install git+https://github.com/Global-B/draft_mail.git
```

## Usage

To use the package, you need to have a Microsoft Graph API access token. You can get one by following the steps in the [Microsoft Graph documentation](https://learn.microsoft.com/en-us/graph/auth-v2-service).

Once you have the access token, you can use the `Graph` class to send draft emails. Here's an example:

```python
from draft_mail import Graph

graph = Graph(access_token)

# Send a draft email
message = await graph.send_draft_email(
    subject="Test email",
    body="This is a test email",
    send_to_email="test@example.com",
)

# Attach a local file to the email
await graph.attach_local_file(message.id, "path/to/file.pdf", "file.pdf")
```

## Contributing

Contributions are welcome!