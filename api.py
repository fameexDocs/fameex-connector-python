import hmac
import hashlib
import time
import json
import logging
from typing import Dict, Optional, Union, Any
from urllib.parse import urlencode
import requests
from requests.exceptions import RequestException

# Constants
BASE_URL = "https://openapi.fameex.net"
CONTENT_TYPE = "application/json"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FameexAPIException(Exception):
    """Custom exception for Fameex API errors"""
    pass

class SignatureGenerator:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret.encode('utf-8')
    
    def generate_signature(self, method: str, request_path: str, body: Optional[Union[Dict, str]] = None) -> Dict[str, str]:
        """
        Generate signature for API request
        
        Args:
            method: HTTP method (GET/POST)
            request_path: API endpoint path
            body: Request body data
            
        Returns:
            Dict containing signature and timestamp
        """
        timestamp = str(int(time.time() * 1000))
        
        sign_payload = timestamp
        sign_payload += method.upper()
        sign_payload += request_path
        
        if body and method.upper() == 'POST':
            if isinstance(body, dict):
                sign_payload += json.dumps(body)
            else:
                sign_payload += body
        
        signature = hmac.new(
            self.api_secret,
            sign_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return {
            'signature': signature,
            'timestamp': timestamp
        }

def send_request(method: str, request_path: str, body: Optional[Dict], api_key: str, api_secret: str) -> Dict[str, Any]:
    """
    Send HTTP request to Fameex API
    
    Args:
        method: HTTP method (GET/POST)
        request_path: API endpoint path
        body: Request body data
        api_key: API key
        api_secret: API secret
        
    Returns:
        API response as dictionary
        
    Raises:
        FameexAPIException: If API request fails
    """
    signer = SignatureGenerator(api_key, api_secret)
    
    if method == "GET" and body:
        request_path += '?' + urlencode(body)
    signature_data = signer.generate_signature(method, request_path, body)
    
    headers = {
        "X-CH-APIKEY": api_key,
        "X-CH-TS": signature_data['timestamp'],
        "X-CH-SIGN": signature_data['signature'],
        "Content-Type": CONTENT_TYPE
    }
    
    url = BASE_URL + request_path
    try:
        if method == "POST":
            response = requests.post(url=url, json=body, headers=headers)
        else:
            response = requests.get(url=url, headers=headers)
        
        response.raise_for_status()
        return response.json()
        
    except RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        raise FameexAPIException(f"API request failed: {str(e)}")

class OrderManager:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret

    def place_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place a new order
        
        Args:
            order: Order details including symbol, volume, side, type, and price
            
        Returns:
            API response
        """
        method = "POST"
        request_path = "/sapi/v1/order"
        body = {
            "symbol": order["symbol"],
            "volume": order["volume"],
            "side": order["side"],
            "type": order["type"],
            "price": order["price"]
        }
        
        return send_request(method, request_path, body, self.api_key, self.api_secret)

    def cancel_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cancel an existing order
        
        Args:
            order: Order details including symbol and order_id
            
        Returns:
            API response
        """
        method = "POST"
        request_path = "/sapi/v1/cancel"
        body = {
            "symbol": order["symbol"],
            "orderId": order["order_id"]
        }
        
        return send_request(method, request_path, body, self.api_key, self.api_secret)

    def open_orders(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get open orders
        
        Args:
            params: Query parameters including symbol and limit
            
        Returns:
            API response
        """
        method = "GET"
        request_path = "/sapi/v1/openOrders"
        body = {
            "symbol": params["symbol"],
            "limit": params["limit"]
        }
        
        return send_request(method, request_path, body, self.api_key, self.api_secret)

class AssetManager:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret

    def balance(self) -> Dict[str, Any]:
        method = "GET"
        request_path = "/sapi/v1/account"
        body = {}

        return send_request(method, request_path, body, self.api_key, self.api_secret)

    def account_balance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        method = "GET"
        request_path = "/sapi/v1/account/balance"
        body = {
            "symbols": params["symbols"]
        }

        return send_request(method, request_path, body, self.api_key, self.api_secret)

if __name__ == "__main__":
    api_key = ""
    api_secret = ""
    order_manager = OrderManager(api_key, api_secret)
    asset_manager = AssetManager(api_key, api_secret)
    
    try:
        # for i in range(100):
        #     start = time.perf_counter()
        #     response = asset_manager.balance()
        #     end = time.perf_counter()
        #     logger.info(f"{response} \n {end - start}s")
        
        # Example usage:
        # Place order
        response = order_manager.place_order({
            "symbol": "ENAUSDT",
            "volume": 10,
            "side": "BUY",
            "type": "LIMIT",
            "price": 0.8374
        })
        logger.info(f"Place order response: {response}")

        # response = order_manager.place_order({
        #     "symbol": "ENAUSDT",
        #     "volume": 14,
        #     "side": "SELL",
        #     "type": "LIMIT",
        #     "price": 0.91
        # })
        # logger.info(f"Place order response: {response}")
        
        # Get open orders
        # response = order_manager.open_orders({
        #     "symbol": "enausdt",
        #     "limit": 20
        # })
        # logger.info(f"Open orders response: {response}")
        
        # Cancel order
        # response = order_manager.cancel_order({
        #     "symbol": "enausdt", 
        #     "order_id": "2602461198832870824"
        # })
        # logger.info(f"Cancel order response: {response}")

        # Get account balance
        # start = time.perf_counter()
        # response = asset_manager.account_balance({"symbols": "USDT,BTC,ETH"})
        # end = time.perf_counter()
        # logger.info(f"{response} \n {end - start}s")
    except FameexAPIException as e:
        logger.error(f"API error occurred: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")