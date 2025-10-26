"""
Alpaca Broker Integration
Handles paper and live trading through Alpaca API
"""

import os
from typing import Dict, Any, Optional

class AlpacaBroker:
    """
    Alpaca broker client for options trading.
    Supports both paper and live trading modes.
    """
    
    def __init__(self, paper: bool = True):
        self.paper = paper
        self.key_id = os.getenv("ALPACA_KEY_ID")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        
        if self.paper:
            self.base_url = os.getenv("ALPACA_API_BASE", "https://paper-api.alpaca.markets")
        else:
            self.base_url = "https://api.alpaca.markets"
            
        self.data_url = os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets/v2")
        
        # Validate credentials
        if not self.key_id or not self.secret_key:
            raise ValueError("ALPACA_KEY_ID and ALPACA_SECRET_KEY must be set")
            
        # Initialize client (mock for now)
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Alpaca trading client."""
        try:
            import alpaca_trade_api as tradeapi
            self.client = tradeapi.REST(
                self.key_id,
                self.secret_key,
                self.base_url,
                api_version='v2'
            )
            print(f"✅ Alpaca client initialized ({'paper' if self.paper else 'live'} mode)")
        except ImportError:
            print("⚠️ alpaca-trade-api not installed, using mock client")
            self.client = None
        except Exception as e:
            print(f"⚠️ Alpaca client initialization failed: {e}")
            self.client = None
    
    def get_account(self) -> Dict[str, Any]:
        """Get account information."""
        if self.client:
            try:
                account = self.client.get_account()
                return {
                    "cash": float(account.cash),
                    "portfolio_value": float(account.portfolio_value),
                    "buying_power": float(account.buying_power),
                    "equity": float(account.equity),
                    "status": account.status
                }
            except Exception as e:
                print(f"⚠️ Error getting account info: {e}")
        
        # Mock account data
        return {
            "cash": 100000.0,
            "portfolio_value": 100000.0,
            "buying_power": 200000.0,
            "equity": 100000.0,
            "status": "ACTIVE"
        }
    
    def submit_order(self, 
                     symbol: str, 
                     side: str, 
                     qty: int, 
                     order_type: str = "market",
                     limit_price: Optional[float] = None) -> Dict[str, Any]:
        """
        Submit a simple stock order (placeholder for options).
        
        Args:
            symbol: Stock symbol
            side: 'buy' or 'sell'
            qty: Quantity
            order_type: 'market' or 'limit'
            limit_price: Price for limit orders
        """
        if self.client:
            try:
                order = self.client.submit_order(
                    symbol=symbol,
                    side=side,
                    type=order_type,
                    qty=qty,
                    time_in_force='DAY',
                    limit_price=limit_price if order_type == 'limit' else None
                )
                return {
                    "id": order.id,
                    "symbol": order.symbol,
                    "side": order.side,
                    "qty": int(order.qty),
                    "status": order.status,
                    "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None
                }
            except Exception as e:
                return {"error": str(e), "symbol": symbol, "side": side, "qty": qty}
        
        # Mock order response
        import uuid
        return {
            "id": str(uuid.uuid4()),
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "status": "NEW",
            "submitted_at": "2025-10-25T13:00:00Z",
            "note": "Mock order - alpaca-trade-api not available"
        }
    
    def submit_options_order(self, 
                           symbol: str, 
                           legs: list, 
                           order_type: str = "market") -> Dict[str, Any]:
        """
        Submit an options order (multi-leg support).
        
        Note: This is a placeholder implementation.
        Real options trading requires proper options API integration.
        """
        # Options trading is not yet fully implemented
        # This is a placeholder that logs the intended trade
        
        order_summary = {
            "symbol": symbol,
            "legs": legs,
            "order_type": order_type,
            "status": "PLACEHOLDER",
            "note": "Options trading not yet implemented - order logged only"
        }
        
        print(f"📋 Options order placeholder: {order_summary}")
        
        return order_summary
    
    def get_positions(self) -> list:
        """Get current positions."""
        if self.client:
            try:
                positions = self.client.list_positions()
                return [
                    {
                        "symbol": pos.symbol,
                        "qty": int(pos.qty),
                        "side": "long" if int(pos.qty) > 0 else "short",
                        "market_value": float(pos.market_value),
                        "cost_basis": float(pos.cost_basis),
                        "unrealized_pl": float(pos.unrealized_pl)
                    }
                    for pos in positions
                ]
            except Exception as e:
                print(f"⚠️ Error getting positions: {e}")
        
        return []  # No positions in mock mode
    
    def get_orders(self, status: str = "all") -> list:
        """Get orders."""
        if self.client:
            try:
                orders = self.client.list_orders(status=status)
                return [
                    {
                        "id": order.id,
                        "symbol": order.symbol,
                        "side": order.side,
                        "qty": int(order.qty),
                        "status": order.status,
                        "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None
                    }
                    for order in orders
                ]
            except Exception as e:
                print(f"⚠️ Error getting orders: {e}")
        
        return []  # No orders in mock mode