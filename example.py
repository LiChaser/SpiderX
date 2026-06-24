from lichauto import LichAuto, auto_crack

def example_simple():
    print("=== Example 1: Simple Usage ===")
    lich = LichAuto()
    
    result = lich.run("http://example.com/login")
    print("Result:", result)

def example_multiple():
    print("\n=== Example 2: Multiple URLs ===")
    lich = LichAuto()
    
    urls = [
        "http://example.com/login",
        "http://test.com/admin"
    ]
    result = lich.run(urls)
    print("Result:", result)

def example_quick():
    print("\n=== Example 3: Quick Function ===")
    result = auto_crack("http://example.com/login")
    print("Result:", result)

def example_get_results():
    print("\n=== Example 4: Get Saved Results ===")
    lich = LichAuto()
    
    results = lich.get_results()
    print("Saved results:", results)

if __name__ == "__main__":
    example_simple()
    example_multiple()
    example_quick()
    example_get_results()
