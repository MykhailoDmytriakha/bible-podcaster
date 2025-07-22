import sys
import argparse
from text_processor import BiblicalContextAnalyzer, TextItem

def run_biblical_context_analysis(input_text: str):
    print("Running biblical context analysis...")
    analyzer = BiblicalContextAnalyzer()
    item = TextItem(content=input_text)
    result_item = analyzer.run(item)
    print("\n--- Biblical Context Analysis Result ---")
    if result_item.context_analysis is not None:
        print(f"Topic: {result_item.context_analysis.topic}")
        print(f"Bible References: {result_item.context_analysis.bible_references}")
        print(f"Keywords: {result_item.context_analysis.keywords}")
        print(f"Result saved in output/{result_item.context_analysis.topic}")
    else:
        print("No context analysis result available.")
    return result_item

def main():
    parser = argparse.ArgumentParser(
        description="Bible Podcaster Pipeline CLI: Analyze biblical thoughts and generate structured context. "
                    "Use -f/--file to specify input file, or provide input via stdin.")
    parser.add_argument('-f', '--file', type=str, help='Path to input text file (if omitted, reads from stdin)')
    args = parser.parse_args()

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            input_text = f.read()
    else:
        print("Enter your biblical thought (end with Ctrl+D):")
        input_text = sys.stdin.read()
    run_biblical_context_analysis(input_text)

if __name__ == "__main__":
    main() 