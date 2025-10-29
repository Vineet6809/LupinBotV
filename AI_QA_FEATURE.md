# 🤖 Lupin AI Q&A Feature Documentation

## Overview
Lupin now includes an AI-powered Q&A assistant that can help you with coding questions, explain code, debug issues, and provide programming guidance. Simply tag Lupin with your question!

## How to Use

### Basic Questions
Tag Lupin anywhere in your message along with your question:
```
@Lupin what is the difference between var, let, and const in JavaScript?
@Lupin explain recursion with an example
@Lupin how do I sort a list in Python?
```

### With Code Files
Upload code files and ask Lupin to analyze them:
```
@Lupin can you review this code?
[Attach: script.py]

@Lupin what does this function do?
[Attach: utils.js]

@Lupin is there a bug in this code?
[Attach: main.java]
```

**Supported file types:**
- Python: `.py`
- JavaScript/TypeScript: `.js`, `.ts`, `.jsx`, `.tsx`
- Java: `.java`
- C/C++: `.c`, `.cpp`, `.h`
- C#: `.cs`
- PHP: `.php`
- Ruby: `.rb`
- Go: `.go`
- Rust: `.rs`
- Swift: `.swift`
- Kotlin: `.kt`
- Scala: `.scala`
- R: `.r`
- Web: `.html`, `.css`, `.scss`, `.xml`
- Config: `.json`, `.yaml`, `.yml`, `.toml`, `.ini`, `.cfg`
- SQL: `.sql`
- Scripts: `.sh`, `.bash`, `.ps1`, `.bat`
- Markdown/Text: `.md`, `.txt`, `.log`

### With Images
Share screenshots of code and ask questions:
```
@Lupin what's wrong with this code?
[Attach: screenshot.png]

@Lupin explain this diagram
[Attach: architecture.jpg]

@Lupin can you help debug this error message?
[Attach: error_screenshot.png]
```

**Supported image types:**
- PNG, JPG, JPEG, WEBP, HEIC, HEIF

### Combining Multiple Attachments
You can attach multiple files and images:
```
@Lupin compare these two implementations
[Attach: version1.py, version2.py]

@Lupin this code gives this error, help me fix it
[Attach: code.js, error_screenshot.png]
```

## Example Use Cases

### 1. Code Explanation
```
@Lupin explain what this code does
[Attach: algorithm.py]
```

**Response**: Lupin will analyze the code and explain its purpose, logic, and any notable patterns.

### 2. Debugging Help
```
@Lupin why am I getting this error?
[Attach: error_screenshot.png]
```

**Response**: Lupin will analyze the error and suggest potential fixes.

### 3. Code Review
```
@Lupin can you review this and suggest improvements?
[Attach: api_handler.js]
```

**Response**: Lupin will review the code and provide suggestions for improvements.

### 4. Concept Explanation
```
@Lupin explain async/await in JavaScript with examples
```

**Response**: Lupin will provide a clear explanation with code examples.

### 5. Best Practices
```
@Lupin what are the best practices for error handling in Python?
```

**Response**: Lupin will provide guidance on best practices.

### 6. Quick Questions
```
@Lupin what is the time complexity of binary search?
@Lupin how do I center a div in CSS?
@Lupin what's the difference between merge sort and quick sort?
```

**Response**: Quick, concise answers to common programming questions.

## Features

### ✨ Smart Context Understanding
- Lupin understands the context of your question
- Analyzes code files and images intelligently
- Provides relevant, targeted responses

### 📁 Multi-File Support
- Upload multiple code files at once
- Lupin will analyze all of them together
- Great for comparing implementations

### 🖼️ Image Analysis
- OCR for code in screenshots
- Error message analysis
- Diagram interpretation

### 💡 Concise Responses
- Answers are kept under 2000 characters
- Clear and to-the-point
- Uses code blocks for code examples

### 🔒 Safe and Reliable
- Powered by Google Gemini AI
- Respects Discord's rate limits
- Shows typing indicator while processing

## Technical Details

### How It Works
1. You tag @Lupin with a question
2. Lupin extracts the question text
3. Downloads and processes any attachments (code files, images)
4. Sends everything to Gemini AI
5. Receives and formats the response
6. Replies to your message with an embed

### Limitations
- **Response length**: Maximum ~1900 characters (Discord limit)
- **File size**: Limited by Discord's upload limits
- **Processing time**: May take a few seconds for complex questions
- **API availability**: Requires valid GEMINI_API_KEY

### Error Handling
If something goes wrong, Lupin will:
- Show a clear error message
- Log the issue for debugging
- Suggest trying again

## Tips for Best Results

### 1. Be Specific
❌ `@Lupin help`
✅ `@Lupin explain what a decorator is in Python`

### 2. Provide Context
❌ `@Lupin fix this`
✅ `@Lupin this code throws a TypeError, can you help me fix it? [attach code]`

### 3. Ask One Question at a Time
❌ `@Lupin explain classes, inheritance, polymorphism, and abstraction`
✅ `@Lupin explain what inheritance is in OOP with an example`

### 4. Use Code Blocks for Inline Code
If you're not attaching a file, use code blocks:
```
@Lupin why does this give an error?
\`\`\`python
def foo():
    return bar
\`\`\`
```

### 5. Reference Specific Parts
For large files:
```
@Lupin can you explain the calculate_total function in this file?
[Attach: shopping_cart.py]
```

## Privacy & Security

- Lupin doesn't store your questions or code
- All processing is done through Gemini AI
- Messages are not logged beyond standard bot logging
- Your code files are temporarily downloaded and then discarded

## Troubleshooting

### Lupin Doesn't Respond
- Make sure you tagged @Lupin correctly
- Check that the bot has permissions to read and send messages
- Verify GEMINI_API_KEY is configured

### "Can't Access AI Capabilities" Error
- The bot needs a valid GEMINI_API_KEY
- Contact your server admin to configure it

### Response is Cut Off
- Responses are limited to ~1900 characters
- Try asking a more specific question
- Break complex questions into smaller parts

### File Not Recognized
- Check that the file extension is supported
- Ensure the file isn't corrupted
- Try uploading it again

## Examples in Action

### Example 1: Python Help
```
User: @Lupin explain list comprehensions in Python

Lupin: 🤖 Lupin AI Assistant
List comprehensions provide a concise way to create lists in Python. 

Basic syntax: [expression for item in iterable if condition]

Examples:
```python
# Square numbers
squares = [x**2 for x in range(10)]

# Filter even numbers
evens = [x for x in range(20) if x % 2 == 0]

# Transform strings
upper = [s.upper() for s in ['hello', 'world']]
```

Benefits: More readable, faster than loops, Pythonic style.
```

### Example 2: Debug Help
```
User: @Lupin why isn't this working?
[Attaches: code.js with async issue]

Lupin: 🤖 Lupin AI Assistant
Looking at your code, the issue is that you're not awaiting the promise. 

Current code:
```javascript
function getData() {
    fetch('/api/data')
    return data  // data is undefined here
}
```

Fix:
```javascript
async function getData() {
    const response = await fetch('/api/data')
    const data = await response.json()
    return data
}
```

The `await` keyword pauses execution until the promise resolves.
```

### Example 3: Image Analysis
```
User: @Lupin what's wrong with this error?
[Attaches: screenshot showing Stack Overflow]

Lupin: 🤖 Lupin AI Assistant
You have a stack overflow error, typically caused by infinite recursion.

Looking at your screenshot, the issue is in the `calculate` function - it calls itself without a base case.

Fix: Add a termination condition:
```python
def calculate(n):
    if n <= 0:  # Base case
        return 0
    return n + calculate(n - 1)
```

Always ensure recursive functions have a stopping condition!
```

## Need More Help?

- Use `/help` to see all bot commands
- Check the main README for general bot usage
- Ask in your server's help channel
- Tag @Lupin with "how do I use you?" for a quick guide

## Powered By
- **Google Gemini AI** (gemini-2.5-flash model)
- Trained on vast amounts of code and programming knowledge
- Constantly improving and learning

---

**Happy coding! 🚀**
