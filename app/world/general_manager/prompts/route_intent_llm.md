Classify the user request into one label only.
Labels: start, status, cancel, result, list, help, unknown.
Examples:
- "start a new job" -> start
- "status 123" -> status
- "cancel 123" -> cancel
- "result 123" -> result
- "list jobs" -> list
- "help" -> help
- "hello" -> unknown
Request: {text}
Return only the label.
