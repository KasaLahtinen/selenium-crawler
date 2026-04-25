import re

with open("Gemini-IRC-bot/bot.py", "r") as f:
    content = f.read()

# Add import
content = content.replace("import yaml", "import yaml\nfrom loguru import logger")

# Remove blessed import and instantiation
content = re.sub(r"from blessed import Terminal\n?", "", content)
content = re.sub(r"term = Terminal\(\)\n?", "", content)

# Replace prints
content = re.sub(r"print\(term\.red\((.*?)\)\)", r"logger.error(\1)", content)
content = re.sub(r"print\(term\.green\((.*?)\)\)", r"logger.info(\1)", content)
content = re.sub(r"print\(term\.yellow\((.*?)\)\)", r"logger.warning(\1)", content)
content = re.sub(r"print\(term\.blue\((.*?)\)\)", r"logger.info(\1)", content)
content = re.sub(r"print\((.*?)\)", r"logger.info(\1)", content)

# There is one specific line:
# print(term.yellow(f"Average ping processing time: {avg_ping_time:.4f} seconds"))
# The above regex will capture it correctly because of the nested parentheses, wait no.
# r'print\(term\.yellow\((.*?)\)\)' will stop at the FIRST closing parenthesis if it's non-greedy `.*?`.
# But `(.*)` might be better, except there are multiple prints on one line? No.
