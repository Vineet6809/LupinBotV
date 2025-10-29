#!/usr/bin/env python3
"""
Test script for Lupin AI Q&A feature.
Tests the answer_question function with various inputs.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, '/app')

async def test_qa_feature():
    """Test the Q&A feature with sample questions."""
    print("=" * 60)
    print("TESTING LUPIN AI Q&A FEATURE")
    print("=" * 60)
    
    # Check if GEMINI_API_KEY is set
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("\n❌ GEMINI_API_KEY not found in environment")
        print("   This feature requires a valid Gemini API key")
        print("   Set it in .env file: GEMINI_API_KEY=your_key_here")
        return False
    
    print(f"\n✅ GEMINI_API_KEY found (starts with: {api_key[:10]}...)")
    
    # Test imports
    print("\n1. Testing imports...")
    try:
        import gemini
        print("   ✅ gemini module imported successfully")
    except Exception as e:
        print(f"   ❌ Failed to import gemini: {e}")
        return False
    
    # Test client initialization
    print("\n2. Testing Gemini client initialization...")
    try:
        client = gemini.get_client()
        if client:
            print("   ✅ Gemini client initialized successfully")
        else:
            print("   ❌ Gemini client is None")
            return False
    except Exception as e:
        print(f"   ❌ Failed to initialize client: {e}")
        return False
    
    # Test simple question
    print("\n3. Testing simple question (this may take a few seconds)...")
    try:
        question = "What is Python?"
        answer = await gemini.answer_question(question)
        
        if answer and not answer.startswith("❌"):
            print(f"   ✅ Got answer (length: {len(answer)} chars)")
            print(f"\n   Question: {question}")
            print(f"   Answer preview: {answer[:200]}...")
        else:
            print(f"   ❌ Failed to get valid answer: {answer[:100]}")
            return False
    except Exception as e:
        print(f"   ❌ Error during question: {e}")
        return False
    
    # Test with code attachment simulation
    print("\n4. Testing with code file simulation...")
    try:
        question = "Explain this code"
        attachments = [{
            'filename': 'test.py',
            'content': 'def hello():\n    print("Hello World")',
            'mime_type': 'text/plain'
        }]
        
        answer = await gemini.answer_question(question, attachments)
        
        if answer and not answer.startswith("❌"):
            print(f"   ✅ Got answer for code file (length: {len(answer)} chars)")
            print(f"   Answer preview: {answer[:200]}...")
        else:
            print(f"   ❌ Failed to get valid answer: {answer[:100]}")
            return False
    except Exception as e:
        print(f"   ❌ Error during code question: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nThe AI Q&A feature is working correctly!")
    print("\nYou can now use it in Discord by tagging @Lupin with questions.")
    print("\nExamples:")
    print("  - @Lupin explain recursion")
    print("  - @Lupin [attach code.py] review this code")
    print("  - @Lupin [attach screenshot.png] what's this error?")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_qa_feature())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
