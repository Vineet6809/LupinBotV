# 🚀 Quick Start - AI Q&A Feature

## What's New?
Lupin can now answer your coding questions! Just tag @Lupin with your question.

## Basic Usage

### 1. Ask a Question
```
@Lupin what is a binary search tree?
```

### 2. Get Help with Code
```
@Lupin explain this code
[Upload: script.py]
```

### 3. Debug with Screenshots
```
@Lupin what's causing this error?
[Upload: error_screenshot.png]
```

## How It Detects Questions

### Just @Lupin = Introduction
```
@Lupin
```
**Result**: Shows bot introduction and features

### @Lupin + Text = AI Answer
```
@Lupin how do I reverse a string in Python?
```
**Result**: AI-powered answer to your question

### @Lupin + Files/Images = AI Analysis
```
@Lupin review this code
[Attach: mycode.py]
```
**Result**: AI analyzes your files and answers

## What Works

✅ **Text questions**
- Explanations
- Best practices
- Comparisons
- How-to questions

✅ **Code files** (20+ languages)
- `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.go`, etc.
- Code review
- Bug detection
- Explanation

✅ **Images**
- Screenshots of code
- Error messages
- Diagrams
- IDE screenshots

✅ **Multiple attachments**
- Multiple files at once
- Files + images together

## Requirements

- ✅ Bot must be online
- ✅ GEMINI_API_KEY must be configured
- ✅ Bot needs message read/send permissions

## Testing

Run this to test if it's working:
```bash
python3 /app/test_qa_feature.py
```

## Tips

1. **Be specific** in your questions
2. **Attach files** for code-related questions
3. **One question at a time** works best
4. **Wait for the typing indicator** - AI takes a few seconds

## Examples

### Example 1: Concept
```
User: @Lupin what's the difference between == and === in JavaScript?

Lupin: 🤖 Lupin AI Assistant
In JavaScript:
- `==` (equality) compares values after type coercion
- `===` (strict equality) compares both value and type

Examples:
5 == "5"  // true (coerces string to number)
5 === "5" // false (different types)

Best practice: Use `===` to avoid unexpected behavior!
```

### Example 2: Code Review
```
User: @Lupin can you review this?
[Attaches: api_handler.py]

Lupin: 🤖 Lupin AI Assistant
Looking at your code:

✅ Good:
- Clear function names
- Error handling present

⚠️ Suggestions:
1. Add input validation for user_id
2. Use async/await for better performance
3. Consider caching frequent queries

Example improvement:
[Shows code example]
```

### Example 3: Debug Help
```
User: @Lupin this gives an error, help!
[Attaches: code.js and error.png]

Lupin: 🤖 Lupin AI Assistant
The error shows "Cannot read property 'map' of undefined"

Issue: `data` is undefined when you try to call `.map()` on it.

Fix: Add a check:
```javascript
if (data && Array.isArray(data)) {
    data.map(item => ...)
}
```

This happens when the API doesn't return data as expected.
```

## See Full Documentation

For more details, see: `/app/AI_QA_FEATURE.md`

---

**Happy coding! 🚀**
