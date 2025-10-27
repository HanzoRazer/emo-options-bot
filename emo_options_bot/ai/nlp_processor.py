"""Natural Language Processing for trading commands."""

from typing import Optional, Dict, Any
import json
import os
from datetime import datetime, timedelta
from decimal import Decimal

from ..core.models import (
    OptionType, OrderAction, StrategyType, TradingStrategy,
    OptionContract, Order
)


class NLPProcessor:
    """
    Process natural language commands and convert them to trading strategies.
    
    Uses AI to understand user intent and extract trading parameters from
    natural language input.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """Initialize NLP processor."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self._use_openai = bool(self.api_key)
        
        if self._use_openai:
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                self._use_openai = False
    
    def parse_command(self, command: str) -> Optional[TradingStrategy]:
        """
        Parse natural language command into a trading strategy.
        
        Args:
            command: Natural language trading command
            
        Returns:
            TradingStrategy object or None if parsing fails
        """
        if self._use_openai:
            return self._parse_with_ai(command)
        else:
            return self._parse_with_rules(command)
    
    def _parse_with_ai(self, command: str) -> Optional[TradingStrategy]:
        """Parse command using OpenAI API."""
        system_prompt = """You are an expert options trading assistant. Parse the user's trading command and extract:
- Action (buy/sell)
- Underlying symbol
- Option type (call/put)
- Strike price
- Expiration date
- Quantity
- Strategy type

Respond with JSON in this format:
{
  "strategy_type": "SINGLE_OPTION",
  "name": "descriptive name",
  "orders": [
    {
      "action": "BUY_TO_OPEN",
      "underlying": "AAPL",
      "strike": 150.0,
      "expiration": "2024-12-20",
      "option_type": "CALL",
      "quantity": 1,
      "limit_price": 5.50
    }
  ],
  "max_risk": 550.0
}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": command}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return self._build_strategy_from_json(result)
        except Exception as e:
            print(f"AI parsing error: {e}")
            return None
    
    def _parse_with_rules(self, command: str) -> Optional[TradingStrategy]:
        """Parse command using rule-based approach (fallback)."""
        command_lower = command.lower()
        
        # Extract action
        if "buy" in command_lower:
            action = OrderAction.BUY_TO_OPEN
        elif "sell" in command_lower:
            action = OrderAction.SELL_TO_OPEN
        else:
            return None
        
        # Extract option type
        if "call" in command_lower:
            option_type = OptionType.CALL
        elif "put" in command_lower:
            option_type = OptionType.PUT
        else:
            return None
        
        # Extract symbol (simple pattern)
        words = command.split()
        symbol = None
        for word in words:
            if word.isupper() and 1 <= len(word) <= 5:
                symbol = word
                break
        
        if not symbol:
            return None
        
        # Extract strike (look for number with $ or "strike")
        strike = None
        for i, word in enumerate(words):
            clean_word = word.replace("$", "").replace(",", "")
            if clean_word.replace(".", "").isdigit():
                strike = Decimal(clean_word)
                break
        
        if not strike:
            return None
        
        # Default expiration (30 days out)
        expiration = (datetime.now() + timedelta(days=30)).date()
        
        # Extract quantity
        quantity = 1
        for i, word in enumerate(words):
            if word.isdigit() and 1 <= int(word) <= 100:
                quantity = int(word)
                break
        
        # Build strategy
        contract = OptionContract(
            symbol=f"{symbol}_{strike}_{option_type.value}_{expiration}",
            underlying=symbol,
            strike=strike,
            expiration=expiration,
            option_type=option_type,
            quantity=quantity
        )
        
        order = Order(
            contract=contract,
            action=action,
            quantity=quantity,
            limit_price=None
        )
        
        max_risk = strike * Decimal(quantity) * Decimal(100)
        
        return TradingStrategy(
            name=f"{action.value} {symbol} {strike} {option_type.value}",
            strategy_type=StrategyType.SINGLE_OPTION,
            orders=[order],
            max_risk=max_risk
        )
    
    def _build_strategy_from_json(self, data: Dict[str, Any]) -> TradingStrategy:
        """Build TradingStrategy from parsed JSON."""
        orders = []
        
        for order_data in data.get("orders", []):
            contract = OptionContract(
                symbol=f"{order_data['underlying']}_{order_data['strike']}_{order_data['option_type']}_{order_data['expiration']}",
                underlying=order_data["underlying"],
                strike=Decimal(str(order_data["strike"])),
                expiration=datetime.fromisoformat(order_data["expiration"]).date(),
                option_type=OptionType[order_data["option_type"]],
                quantity=order_data.get("quantity", 1)
            )
            
            order = Order(
                contract=contract,
                action=OrderAction[order_data["action"]],
                quantity=order_data.get("quantity", 1),
                limit_price=Decimal(str(order_data["limit_price"])) if order_data.get("limit_price") else None
            )
            orders.append(order)
        
        return TradingStrategy(
            name=data.get("name", "AI Generated Strategy"),
            strategy_type=StrategyType[data.get("strategy_type", "SINGLE_OPTION")],
            orders=orders,
            max_risk=Decimal(str(data.get("max_risk", 0)))
        )
