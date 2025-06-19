import argparse
import os

def minimal_main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", default="scripts/output_large.txt") # Changed default
    args = parser.parse_args()

    output_dir = os.path.dirname(args.filename)
    if output_dir and not os.path.exists(output_dir):
        print(f"TEST_WRITER: Creating directory {{output_dir}}")
        os.makedirs(output_dir) # Added directory creation

    # Target ~40KB. Each line is 43 bytes. 40000 / 43 = ~930 lines.
    content = "Hello from test_writer.py. This is a line.\n" * 930

    try:
        with open(args.filename, "w") as f:
            f.write(content)
        print(f"TEST_WRITER: Successfully wrote to {{args.filename}} (Size: {{len(content)}} bytes)")
    except Exception as e:
        print(f"TEST_WRITER: Error writing file: {{e}}")

if __name__ == "__main__":
    minimal_main()
