"""
Example 1: Basic Usage - Simple Option Trade

This example demonstrates the basic workflow of processing a simple
option trade command.
"""

from emo_options_bot import EMOOptionsBot


def main():
    # Initialize the bot
    print("Initializing EMO Options Bot...")
    bot = EMOOptionsBot()
    
    # Process a simple trading command
    print("\nProcessing command: 'Buy 1 AAPL call at $150'")
    result = bot.process_command("Buy 1 AAPL call at $150")
    
    # Check if successful
    if result["success"]:
        print("\n✓ Command processed successfully!")
        print(f"  Strategy ID: {result['strategy_id']}")
        print(f"  Strategy: {result['strategy']['name']}")
        print(f"  Type: {result['strategy']['strategy_type']}")
        print(f"  Orders: {len(result['strategy']['orders'])}")
        
        # Risk assessment
        risk = result['risk_assessment']
        print(f"\n  Risk Assessment:")
        print(f"    Approved: {risk['approved']}")
        print(f"    Risk Score: {risk['risk_score']:.1f}/100")
        print(f"    Max Loss: ${risk['max_loss']}")
        
        # Approve the strategy
        strategy_id = result['strategy_id']
        print(f"\nApproving strategy {strategy_id}...")
        approval = bot.approve_strategy(strategy_id)
        
        if approval['success']:
            print("✓ Strategy approved!")
            print(f"  {approval['message']}")
        else:
            print(f"✗ Approval failed: {approval['error']}")
    else:
        print("\n✗ Command processing failed!")
        print(f"  Error: {result['error']}")


if __name__ == "__main__":
    main()
