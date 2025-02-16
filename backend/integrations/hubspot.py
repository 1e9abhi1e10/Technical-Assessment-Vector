import logging
from fastapi import Request
from fastapi.responses import HTMLResponse
import httpx
import json
import os
from dotenv import load_dotenv
from redis_client import add_key_value_redis, get_value_redis
from .integration_item import IntegrationItem
from datetime import datetime

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

HUBSPOT_CLIENT_ID = os.getenv("HUBSPOT_CLIENT_ID")
HUBSPOT_CLIENT_SECRET = os.getenv("HUBSPOT_CLIENT_SECRET")
HUBSPOT_REDIRECT_URI = os.getenv("HUBSPOT_REDIRECT_URI")

if not all([HUBSPOT_CLIENT_ID, HUBSPOT_CLIENT_SECRET, HUBSPOT_REDIRECT_URI]):
    raise ValueError("Missing required HubSpot environment variables")


async def authorize_hubspot(user_id, org_id):
    """Generate HubSpot OAuth authorization URL."""
    state = f"{user_id}_{org_id}"
    auth_url = (
        f"https://app.hubspot.com/oauth/authorize?"
        f"client_id={HUBSPOT_CLIENT_ID}&"
        f"redirect_uri={HUBSPOT_REDIRECT_URI}&"
        f"scope=crm.objects.contacts.read%20crm.objects.contacts.write&"
        f"state={state}"
    )
    return {"authorization_url": auth_url}


async def oauth2callback_hubspot(request: Request):
    """Handle OAuth callback and store credentials in Redis."""
    code = request.query_params.get("code")
    state = request.query_params.get("state", "")

    if not code:
        return {"error": "Authorization code not found"}

    try:
        user_id, org_id = state.split("_")
    except ValueError:
        return {"error": "Invalid state parameter"}

    token_url = "https://api.hubapi.com/oauth/v1/token"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "client_id": HUBSPOT_CLIENT_ID,
                    "client_secret": HUBSPOT_CLIENT_SECRET,
                    "redirect_uri": HUBSPOT_REDIRECT_URI,
                    "code": code,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            response_json = response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to retrieve access token: {e.response.text}")
        return {"error": e.response.text}

    except json.JSONDecodeError:
        logger.error("Invalid JSON response from HubSpot token endpoint.")
        return {"error": "Invalid response from HubSpot"}

    # Store credentials in Redis
    redis_key = f"hubspot_credentials_{user_id}_{org_id}"
    await add_key_value_redis(
        redis_key, json.dumps(response_json), expire=response_json.get("expires_in", 1800)
    )

    return HTMLResponse(content="""
            <html>
            <head>
                <title>HubSpot Authorization Success</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        background-color: #f5f8fa;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                    }
                    .container {
                        background: white;
                        padding: 2rem;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                        text-align: center;
                        max-width: 400px;
                    }
                    .success-icon {
                        color: #00bf8f;
                        font-size: 48px;
                        margin-bottom: 1rem;
                    }
                    h1 {
                        color: #33475b;
                        font-size: 24px;
                        margin-bottom: 1rem;
                    }
                    p {
                        color: #516f90;
                        margin-bottom: 1.5rem;
                    }
                    .close-message {
                        color: #8795a1;
                        font-size: 14px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success-icon">✓</div>
                    <h1>Authorization Successful!</h1>
                    <p>Your HubSpot account has been successfully connected.</p>
                    <p class="close-message">This window will close automatically...</p>
                </div>
                <script>
                    setTimeout(function() {
                        window.close();
                    }, 2000);
                </script>
            </body>
            </html>
        """)


async def get_hubspot_credentials(user_id, org_id):
    """Retrieve stored HubSpot credentials from Redis."""
    redis_key = f"hubspot_credentials_{user_id}_{org_id}"
    stored_credentials = await get_value_redis(redis_key)

    if stored_credentials:
        try:
            credentials = json.loads(stored_credentials)
            if "access_token" in credentials:
                return credentials
        except json.JSONDecodeError:
            logger.error("Failed to parse stored HubSpot credentials.")

    return {"error": "No valid credentials found. Please authorize HubSpot."}


async def get_items_hubspot(credentials):
    """Fetch contacts from HubSpot and convert them to IntegrationItems."""
    try:
        credentials_dict = json.loads(credentials) if isinstance(credentials, str) else credentials
        access_token = credentials_dict.get("access_token")

        if not access_token:
            return {"error": "Access token is missing"}

        properties = [
            "email", "firstname", "lastname", "phone",
            "company", "website", "address", "city",
            "state", "country", "createdate", "lastmodifieddate",
            "jobtitle", "lifecyclestage", "lead_status",
            "mobilephone", "industry"
        ]

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.hubapi.com/crm/v3/objects/contacts",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                params={
                    "properties": properties,
                    "limit": 100,
                    "archived": False
                }
            )
            response.raise_for_status()
            data = response.json()

        integration_items = []

        for contact in data.get("results", []):
            props = contact.get("properties", {})

            metadata = {
                "hubspot_id": contact.get("id"),
                "created_at": props.get("createdate"),
                "updated_at": props.get("lastmodifieddate"),
                "company": props.get("company"),
                "website": props.get("website"),
                "address": props.get("address"),
                "city": props.get("city"),
                "state": props.get("state"),
                "country": props.get("country"),
                "phone": props.get("phone"),
                "mobile_phone": props.get("mobilephone"),
                "job_title": props.get("jobtitle"),
                "industry": props.get("industry"),
                "lifecycle_stage": props.get("lifecyclestage"),
                "lead_status": props.get("lead_status"),
                "description": f"Contact at {props.get('company', 'No Company')}",
            }

            # Parse timestamps safely
            creation_time = (
                datetime.fromisoformat(props["createdate"].replace("Z", "+00:00"))
                if "createdate" in props else None
            )
            last_modified_time = (
                datetime.fromisoformat(props["lastmodifieddate"].replace("Z", "+00:00"))
                if "lastmodifieddate" in props else None
            )

            item = IntegrationItem(
                id=contact.get("id"),
                type="contact",
                name=f"{props.get('firstname', '')} {props.get('lastname', '')}".strip(),
                email=props.get("email"),
                creation_time=creation_time,
                last_modified_time=last_modified_time,
                metadata=metadata,
                raw_data=contact,
                visibility=True
            )

            integration_items.append(item)

        logger.info(f"Retrieved {len(integration_items)} contacts from HubSpot")
        return integration_items

    except httpx.HTTPStatusError as e:
        logger.error(f"HubSpot API Error: {e.response.text}")
        return {"error": e.response.text}

    except Exception as e:
        logger.error(f"Error in get_items_hubspot: {str(e)}")
        return {"error": str(e)}
