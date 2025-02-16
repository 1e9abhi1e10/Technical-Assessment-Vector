# HubSpot, Airtable, Notion OAuth Integration

## Overview
This project implements OAuth integrations with **HubSpot, Airtable, and Notion** using a **FastAPI backend** and **React frontend**. The main focus is on handling OAuth authentication and retrieving data securely.

## Prerequisites

- **Python** 3.8 or higher
- **Node.js** 14 or higher
- **Redis server** (Local or [Upstash](https://upstash.com/))
- **HubSpot Developer Account**

---

## **Project Structure**
```
/
├── frontend/
│   ├── src/
│   │   ├── integrations/
│   │   │   ├── airtable.js
│   │   │   ├── notion.js
│   │   │   ├── hubspot.js
│   ├── package.json
│   ├── App.js
│   ├── index.js
├── backend/
│   ├── integrations/
│   │   ├── airtable.py
│   │   ├── notion.py
│   │   ├── hubspot.py
│   ├── main.py
│   ├── .env
└── README.md
```

---

## Setup Instructions

### 1. HubSpot Setup

#### **Create a HubSpot Developer Account:**  
1. Go to the [HubSpot Developer Portal](https://developers.hubspot.com/).  
2. Sign up or log in to your HubSpot account.  
3. Navigate to **"Apps"** and create a new app.  

#### **Configure OAuth Settings:**  
1. In your HubSpot app settings, go to **Auth Settings** → **OAuth**.  
2. Add the following **Redirect URL**:  
   ```
   http://localhost:8000/integrations/hubspot/oauth2callback
   ```
3. Copy your **Client ID** and **Client Secret**.  

#### **Required Scopes**  
The following scopes are required based on the `authorize_hubspot` function in `hubspot.py`:  

| Scope                           | Purpose |
|---------------------------------|---------|
| `crm.objects.contacts.read`     | Read access to contacts |
| `crm.objects.contacts.write`    | Write access to contacts |

To configure these scopes:  
1. Open your **HubSpot App** → **Auth Settings**.  
2. Under **Scopes**, select:  
   - `crm.objects.contacts.read`  
   - `crm.objects.contacts.write`  
3. Save the settings before testing the OAuth flow.  

---

### 2. Backend Setup
1. Clone the repository and navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install fastapi uvicorn httpx python-dotenv redis
   ```
4. Create a `.env` file in the backend directory:
   ```env
    HUBSPOT_CLIENT_ID=your_hubspot_client_id
    HUBSPOT_CLIENT_SECRET=your_hubspot_client_secret
    HUBSPOT_REDIRECT_URI=http://localhost:8000/integrations/hubspot/oauth2callback

    REDIS_HOST=localhost
    REDIS_PORT=6379
   ```
5. Start Redis server:
   ```bash
   # On Windows:
   redis-server

   # On Mac with Homebrew:
   brew services start redis

   # On Linux:
   sudo service redis-server start
   ```
6. Start the backend server in other terminal:
   ```bash
   uvicorn main:app --reload
   ```
   The backend will run on `http://localhost:8000`

### 3. Frontend Setup
1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the frontend development server:
   ```bash
   npm start
   ```
   The frontend will run on `http://localhost:3000`

---


## **OAuth Workflow**  

### **Step 1: User Initiates OAuth Login**  
- The frontend displays a **"Connect to HubSpot"** button.  
- Clicking the button redirects the user to **HubSpot's authorization URL**.  

### **Step 2: Authorization Request**  
- The request includes:
  - **Client ID**
  - **Redirect URI**
  - **State parameter (for CSRF protection)**  
- The user logs in and grants access.  

### **Step 3: HubSpot Redirects Back**  
- After authorization, HubSpot redirects to:  
  ```
  http://localhost:8000/integrations/hubspot/oauth2callback?code=AUTH_CODE&state=STATE_VALUE
  ```
- The backend validates the **state parameter** using Redis.  

### **Step 4: Exchange Authorization Code for Access Token**  
- The backend sends a request to **HubSpot’s Token API** to get:  
  - **Access token** (short-lived)
  - **Refresh token** (for re-authentication)
- The tokens are securely stored in Redis.  

### **Step 5: Fetch User Data from HubSpot API**  
- The access token is used to retrieve **contacts, companies, and deals** from HubSpot.  
- Data is serialized to an `IntegrationItem` format.  
- The frontend displays the retrieved data.  

---

## Data Retrieval
- After authentication, the system **fetches contacts from HubSpot**.
- Contact data is **serialized into `IntegrationItem` format**.
- Results can be **viewed in the console output**.

---

## Security Considerations
- **CSRF Protection**: Implemented via state parameter.
- **Secure Credential Storage**: Uses Redis KV store.
- **TLS/SSL Encryption**: Configured for Redis communication.
- **Rate Limits**: HubSpot API rate limits are handled efficiently.

---

## Troubleshooting

### 1. Redis Connection Issues
- Verify Redis is running: `redis-cli ping`
- Check Redis connection settings in `.env`

### 2. OAuth Errors
- Ensure the **Client ID and Secret** are correct
- Verify **redirect URI** in HubSpot app settings
- Clear browser cache and retry

### 3. API Rate Limits
- HubSpot has rate limits for API calls
- Check response headers for rate limit details

---

## Additional Notes
- **OAuth credentials** automatically expire and are refreshed.
- **Frontend UI** displays both success and failure states.
- **Error messages** are handled properly for debugging.
