import sys
import argparse
from text_processor import BiblicalContextAnalyzer, TextItem
from audio_generator import ElevenLabsTTS
from image_generator import SimpleCardGenerator
from video_creator import SimpleVideoCreator
from youtube_uploader import YouTubeUploader
from config.logging_config import setup_logging
from config.config import settings

def run_biblical_context_analysis(input_text: str):
    print("\n\nRunning biblical context analysis...")
    analyzer = BiblicalContextAnalyzer()
    item = TextItem(content=input_text)
    result_item = analyzer.run(item)
    print("\n--- Biblical Context Analysis Result ---")
    if result_item.context_analysis is not None:
        analysis = result_item.context_analysis
        print(f"Topic: {analysis.topic}")
        print(f"Summary: {analysis.summary}")
        
        print(f"\nKeywords ({len(analysis.keywords)}): {', '.join(analysis.keywords)}")
        
        if analysis.themes:
            print(f"Themes ({len(analysis.themes)}): {', '.join(analysis.themes)}")
        
        if analysis.structure:
            print(f"Structure: {analysis.structure}")
        
        if analysis.typologies_and_parallelisms:
            print(f"Typologies & Parallelisms ({len(analysis.typologies_and_parallelisms)}):")
            for tp in analysis.typologies_and_parallelisms:
                print(f"  - {tp}")
        
        if analysis.bible_references:
            print(f"\nBible References ({len(analysis.bible_references)}):")
            for ref in analysis.bible_references:
                print(f"  📖 {ref.reference}")
                print(f"     Context: {ref.context}")
                for quote in ref.quotes:
                    print(f"     Quote: \"{quote}\"")
                print()
        else:
            print("\nBible References: None found")
        
        # Display context sufficiency information
        print(f"\n--- Context Sufficiency Assessment ---")
        print(f"Completeness Score: {analysis.context_evaluation.completeness_score:.2f}/1.0")
        print(f"Thought Completeness: {analysis.context_evaluation.thought_completeness}")
        print(f"Context Sufficient: {'✅ Yes' if analysis.context_evaluation.is_context_sufficient else '❌ No'}")
        
        if analysis.context_evaluation.missing_elements:
            print(f"Missing Elements: {', '.join(analysis.context_evaluation.missing_elements)}")
        
        if analysis.context_evaluation.enrichment_suggestions:
            print(f"Enrichment Suggestions: {', '.join(analysis.context_evaluation.enrichment_suggestions)}")
        
        print(f"\nResult saved in output/{analysis.topic}")
    else:
        print("No context analysis result available.")
    return result_item

def create_context_enrichment_system(analysis_result: TextItem):
    print("\n\nCreating context enrichment system...")
    
    if analysis_result.context_analysis is None:
        print("No context analysis available for enrichment.")
        return analysis_result
    
    analysis = analysis_result.context_analysis
    
    # Check if context is sufficient
    if analysis.context_evaluation.is_context_sufficient:
        print(f"✅ Context is sufficient (score: {analysis.context_evaluation.completeness_score:.2f})")
        print(f"Thought completeness: {analysis.context_evaluation.thought_completeness}")
        return analysis_result
    
    # Context needs enrichment
    print(f"⚠️  Context needs enrichment (score: {analysis.context_evaluation.completeness_score:.2f})")
    print(f"Thought completeness: {analysis.context_evaluation.thought_completeness}")
    
    if analysis.context_evaluation.missing_elements:
        print(f"Missing elements: {', '.join(analysis.context_evaluation.missing_elements)}")
    
    if analysis.context_evaluation.enrichment_suggestions:
        print(f"Enrichment suggestions: {', '.join(analysis.context_evaluation.enrichment_suggestions)}")
    
    # TODO: Implement actual enrichment logic
    # This could involve:
    # 1. Generating additional biblical references based on themes
    # 2. Expanding keywords and themes
    # 3. Creating structure where missing
    # 4. Adding supporting content
    
    print("Enrichment system placeholder - actual implementation needed")
    return analysis_result


def run_pipeline(input_text: str):
    setup_logging()
    # 1) Text analysis
    text_item = run_biblical_context_analysis(input_text)

    # 2) Audio generation
    tts = ElevenLabsTTS()
    audio_item = tts.run(text_item)

    # 3) Image generation
    img_gen = SimpleCardGenerator()
    image_item = img_gen.run(text_item)

    # 4) Video creation
    video_maker = SimpleVideoCreator()
    video_item = video_maker.run((audio_item, image_item))

    # 5) YouTube (MVP: write metadata only)
    uploader = YouTubeUploader()
    uploader.run(video_item)

    print(f"\nPipeline completed. Video: {video_item.path}\n")

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
        
    run_pipeline(input_text)

if __name__ == "__main__":
    main() 