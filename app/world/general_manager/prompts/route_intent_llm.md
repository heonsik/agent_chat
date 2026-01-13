Classify the user request into one label only.
Labels: status, cancel, result, list, help, start.
Examples:
- "/status 123" -> status
- "/cancel 123" -> cancel
- "/result 123" -> result
- "/list" -> list
- "/help" -> help
- "show project structure" -> start
- "who are you" -> start
Request: {text}
Return only the label.
