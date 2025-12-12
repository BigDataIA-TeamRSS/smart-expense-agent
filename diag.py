# diagnostic.py
import os

print("Current directory:", os.getcwd())
print("\ntools/ folder contents:")
print("-" * 50)

tools_dir = "tools"
if os.path.exists(tools_dir):
    for file in os.listdir(tools_dir):
        if file.endswith('.py'):
            filepath = os.path.join(tools_dir, file)
            print(f"\n📄 {file}")
            
            # Read first 30 lines safely using UTF-8
            try:
                with open(filepath, 'r', encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f, 1):
                        if i > 30:
                            break
                        if 'def ' in line and '(' in line:
                            print(f"   → {line.strip()}")
            except Exception as e:
                print(f"   ❌ Error reading file: {e}")
else:
    print("tools/ folder not found!")

print("\n" + "-" * 50)
