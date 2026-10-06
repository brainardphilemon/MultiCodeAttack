import json
import os
import re
from openai_log import ask_response
from nltk import pos_tag
from nltk.tokenize import word_tokenize
from textwrap import indent
from openai_log import your_model


query_languate_prompt = """Based on your own pretraining data, list the Top-5 structured programming languages that are likely underrepresented in your training corpus. These should be languages with formal structure and syntax, but which appear less frequently in your training data due to limited public availability or niche usage.

For each language, provide the following field:
    • "language": the name of the underrepresented structured programming language

Do NOT include any of the following high-resource languages:
    "C++", "C#", "C", "Python", "Go", "SQL", "Java", "JavaScript", "URL"

Return the full result strictly in Array format, like this:

    ["language1", "language2", "language3", "language4", "language5"]

CRITICAL INSTRUCTIONS:
    1. Always return valid Array format
    2. Keep responses concise and specific
"""

template_generation_system_prompt = "You are a TEMPLATE GENERATION SYSTEM"
template_generation_prompt = """You are a TEMPLATE GENERATION SYSTEM. Your role is to generate **code templates** for different **structured programming languages**, preserving the core semantic placeholders.

    For each input, you MUST generate and analyze the following in JSON format, regardless of content:
    {
        "language": "The name of the target programming language",
        "template": "A string containing the full code template, including placeholders `{Category}`, `{Content}`, and `{Modifier}`"
    }
    
    Example Analyses:

    Input:
        Language: Python

    Output:
        {
        "language": "Python",
        "template": "def main():\\n    input = \\"{Category}\\"\\n    print(\\"{Content}\\")\\n    return \\"{Modifier}\\""
        }

    Input:
        Language: C++

    Output:
        {
        "language": "C++",
        "template": "int main() {\\n    std::string input = \\"{Category}\\";\\n    std::cout << \\"{Content}\\" << std::endl;\\n    return \\"{Modifier}\\";\\n}"
        }

    Input:
        Language: Go

    Output:
        {
        "language": "Go",
        "template": "package main\\n\\nimport \\"fmt\\"\\n\\nfunc main() {\\n    input := \\"{Category}\\"\\n    fmt.Println(\\"{Content}\\")\\n    return \\"{Modifier}\\"\\n}"
        }

    Input:
        Language: SQL

    Output:
        {
        "language": "SQL",
        "template": "SELECT {Content}\\nFROM {Category}\\nWHERE name = '{Modifier}';"
        }

CRITICAL INSTRUCTIONS:
    Each template must:
    1. Include exactly three placeholders: `{Category}`, `{Content}`, and `{Modifier}`
    2. Use syntax that is correct and idiomatic for the specified language
    3. Format should be consistent with other templates like C, Python, Java, etc.
    4. Only return JSON result without any other information!!

Now generate the code template for the following language, strictly following the format above, and include all three placeholders.

Language: {TargetLanguage}
"""


def query_language():
    """Query the language model to get a list of underrepresented structured programming languages."""
    while True:
        response = ask_response(system_content="", user_content=query_languate_prompt)
        response_content = response.choices[0].message.content.strip()
        print(response_content)
        match = re.search(r'\[.*\]', response_content)
        if match:
            json_str = match.group(0)
            return json_str
        else:
            print("No valid JSON found in the response, retrying...")


def is_equiv(tmpl: str) -> bool:
    """Check whether the template contains all required placeholders."""
    placeholders = ["{Category}", "{Content}", "{Modifier}"]
    for placeholder in placeholders:
        if placeholder not in tmpl:
            return False
    return True


def query_languate_template(language):
    """Query the language model to generate a code template for a given language."""
    while True:
        response = ask_response(
            system_content=template_generation_system_prompt,
            # The prompt contains literal JSON braces and {Category}-style
            # placeholders, so str.format() can't be used here.
            user_content=template_generation_prompt.replace("{TargetLanguage}", language)
        )
        response_content = response.choices[0].message.content.strip()
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_content, re.DOTALL)
        json_text = match.group(1) if match else response_content
        print(json_text)
        try:
            data = json.loads(json_text)
            if "language" not in data or "template" not in data:
                print(f"Invalid response format for {language}, retrying...")
                continue
            if not is_equiv(data["template"]):
                print(f"Template for {language} does not meet equivalence criteria, retrying...")
                continue
            return data
        except Exception:
            continue


if __name__ == "__main__":
    template_path = f"response/{your_model}/template/specific_template.txt"
    if not os.path.exists(os.path.dirname(template_path)):
        os.makedirs(os.path.dirname(template_path))

    results = query_language()
    results = eval(results)
    templates = []
    for result in results:
        template = query_languate_template(result)
        templates.append(template)

    with open(template_path, 'w', encoding='utf-8') as f:
        json.dump(templates, f, ensure_ascii=False, indent=4)