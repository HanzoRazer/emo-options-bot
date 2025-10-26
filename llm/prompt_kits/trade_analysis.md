# Trade Analysis Prompt Template

## Analysis Request

**User Request**: {user_request}

## Analysis Framework

Please conduct a comprehensive analysis of this trading request following these steps:

### 1. Market Assessment
Use available tools to gather current data:
- Current price and recent performance
- Implied volatility rank and percentiles
- Volume and liquidity metrics
- Upcoming events (earnings, ex-dividend dates)

### 2. Outlook Development
Based on the data and request:
- Determine market outlook (bullish/bearish/neutral/volatile/calm)
- Assess confidence in outlook
- Identify key drivers and assumptions

### 3. Strategy Selection
Choose the most appropriate strategy considering:
- Market outlook and volatility environment
- Risk tolerance specified or implied
- Time horizon and objectives
- Account constraints

### 4. Risk Analysis
Thoroughly assess risks:
- Maximum loss scenarios
- Probability of profit
- Key market risks (direction, volatility, time)
- External risks (events, liquidity, slippage)
- Mitigation strategies for each risk

### 5. Position Sizing
Calculate appropriate size based on:
- Maximum acceptable loss (default: 2% of account)
- Strategy risk profile
- Account margin requirements
- Diversification considerations

## Output Requirements

Provide your analysis as a valid JSON object matching the TradePlan schema with:

1. **Complete Rationale**: 
   - Clear summary of reasoning
   - Key factors driving the decision
   - Specific data citations with timestamps
   - Confidence assessment

2. **Risk Assessment**:
   - Detailed "what could go wrong" analysis
   - Probability estimates for each risk
   - Specific mitigation strategies

3. **Data Citations**:
   - Source of each data point
   - Actual values retrieved
   - Confidence in data quality
   - Timestamp of retrieval

4. **Constraints**:
   - Maximum loss percentage
   - Margin requirements
   - Liquidity minimums
   - Event avoidance rules

## Example Data Citation Format

```json
{
  "source": "market_data_api",
  "value": 0.35,
  "timestamp": "2025-10-25T10:30:00Z",
  "confidence": 0.9
}
```

## Risk Mitigation Example

```json
{
  "risk": "Earnings announcement surprise",
  "mitigation": "Close position 2 days before earnings or use smaller size",
  "probability": 0.25,
  "impact": "High - could cause 50%+ loss"
}
```

Begin your analysis now, using the available tools to gather current market data.