import json
import os
from datetime import datetime, timezone


def handler(event, context):
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
    }

    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": ""}

    return {
        "statusCode": 200,
        "headers": headers,
        "body": json.dumps({
            "status": "ok",
            "service": "NTE Content Bot",
            "gemini_configured": bool(os.environ.get("GEMINI_API_KEY")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoints": {
                "content": "/.netlify/functions/content?limit=6&platform=reddit",
                "health":  "/.netlify/functions/health"
            }
        })
    }