import re


TOKENS = {
    "reservedword": r"\b(int|float|void|return|if|while|cin|cout|include|using|namespace|std|main)\b",
    "identifier": r"\b[a-zA-Z_][a-zA-Z0-9_]*\b",
    "number": r"\b\d+\b",
    "symbol": r"[+\-*/<>=!;,{}()\[\]]",
    "string": r'"[^"]*"'
}

# CFG 
GRAMMAR = {
    "Start": [["S", "N", "M"]],
    "S": [["#include", "S"], ["ε"]],
    "N": [["using namespace std;"], ["ε"]],
    "M": [["int main(){", "T", "V", "}"]],
    "T": [["Id", "T"], ["L", "T"], ["Loop", "T"], ["Input", "T"], ["Output", "T"], ["ε"]],
    "V": [["return 0;"], ["ε"]],
    "Id": [["int", "L"], ["float", "L"]],
    "L": [["identifier", "Assign", "Z"]],
    "Z": [[",", "identifier", "Assign", "Z"], [";"]],
    "Assign": [["=", "Operation"], ["ε"]],
    "Operation": [["number", "P"], ["identifier", "P"]],
    "P": [["O", "W", "P"], ["ε"]],
    "O": [["+"], ["-"], ["*"]],
    "W": [["number"], ["identifier"]],
    "Expression": [["Operation", "K", "Operation"]],
    "K": [["=="], [">="], ["<="], ["!="]],
    "Loop": [["while(", "Expression", "){", "T", "}"]],
    "Input": [["cin", ">>", "identifier", "F", ";"]],
    "F": [[">>", "identifier", "F"], ["ε"]],
    "Output": [["cout", "<<", "C", "H", ";"]],
    "H": [["<<", "C", "H"], ["ε"]],
    "C": [["number"], ["string"], ["identifier"]]
}

FIRST = {}
FOLLOW = {}

def compute_first():
    for non_terminal in GRAMMAR:
        FIRST[non_terminal] = set()

    while True:
        updated = False
        for non_terminal, productions in GRAMMAR.items():
            for production in productions:
                for symbol in production:
                    if symbol in GRAMMAR:  
                        new_firsts = FIRST[symbol] - {"ε"}
                        if new_firsts - FIRST[non_terminal]:
                            FIRST[non_terminal].update(new_firsts)
                            updated = True
                        if "ε" not in FIRST[symbol]:
                            break
                    else:  # Terminal
                        if symbol not in FIRST[non_terminal]:
                            FIRST[non_terminal].add(symbol)
                            updated = True
                        break
                else:
                    if "ε" not in FIRST[non_terminal]:
                        FIRST[non_terminal].add("ε")
                        updated = True
        if not updated:
            break

def compute_follow():
    for non_terminal in GRAMMAR:
        FOLLOW[non_terminal] = set()
    FOLLOW["Start"].add("$")  

    while True:
        updated = False
        for non_terminal, productions in GRAMMAR.items():
            for production in productions:
                trailer = FOLLOW[non_terminal]
                for symbol in reversed(production):
                    if symbol in GRAMMAR:  
                        if trailer - FOLLOW[symbol]:
                            FOLLOW[symbol].update(trailer)
                            updated = True
                        if "ε" in FIRST[symbol]:
                            trailer = trailer.union(FIRST[symbol] - {"ε"})
                        else:
                            trailer = FIRST[symbol]
                    else:
                        trailer = {symbol}
        if not updated:
            break

def build_parse_table():
    parse_table = {non_terminal: {} for non_terminal in GRAMMAR}
    for non_terminal, productions in GRAMMAR.items():
        for production in productions:
            firsts = set()
            for symbol in production:
                if symbol in GRAMMAR:
                    firsts.update(FIRST[symbol] - {"ε"})
                    if "ε" not in FIRST[symbol]:
                        break
                else:
                    firsts.add(symbol)
                    break
            else:
                firsts.add("ε")

            for terminal in firsts:
                if terminal != "ε":
                    parse_table[non_terminal][terminal] = production
            if "ε" in firsts:
                for terminal in FOLLOW[non_terminal]:
                    parse_table[non_terminal][terminal] = production

    return parse_table

def tokenize(code):
    tokens = []
    seen_tokens = set()  

    for token_name, token_regex in TOKENS.items():
        matches = re.finditer(token_regex, code)
        for match in matches:
            token_value = match.group(0)

            if (token_name, token_value) not in seen_tokens:
                tokens.append((token_name, token_value))
                seen_tokens.add((token_name, token_value))

    return tokens

def create_token_table(tokens):
    token_table = []

    token_order = ["string", "number", "symbol", "identifier", "reservedword"]
    
    for token_type in token_order:
        filtered_tokens = [t[1] for t in tokens if t[0] == token_type]
        filtered_tokens.sort()

        for token_value in filtered_tokens:
            # Calculate hash for each token
            hash_value = hash(token_value)
            # Add to the token table
            token_table.append({
                "Token Name": token_type,
                "Token Value": token_value,
                "Hash Value": hash_value
            })

    return token_table

def check_errors(code):
    """
    Checks the code for common syntax errors:
    1. Invalid assignments (e.g., int x = cppiler;)
    2. Missing semicolons (;)
    """
    lines = code.split("\n")  # Split code into lines
    errors = []  # List to store error messages

    for line_no, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:  # Skip empty lines
            continue

        # Check for invalid assignments (e.g., int x = cppiler;)
        invalid_assignment = re.search(r"\b(int|float)\b\s+\w+\s*=\s*\w+\s*;", line)
        if invalid_assignment:
            # Ensure the right-hand side of the assignment is a number or identifier
            rhs = invalid_assignment.group(0).split('=')[1].strip(' ;')
            if not re.match(r"^\d+(\.\d+)?$|^[a-zA-Z_][a-zA-Z0-9_]*$", rhs):
                errors.append(f"Error: Invalid assignment on line {line_no}: '{line}'")

        # Check for missing semicolon (;)
        if not line.endswith(";") and not line.endswith("{") and not line.endswith("}") and "(" not in line:
            errors.append(f"Error: Missing semicolon on line {line_no}: '{line}'")

    return errors


def process_code(code):
    # Step 1: Check for errors in the code
    errors = check_errors(code)
    if errors:
        print("\nErrors found in the code:")
        for error in errors:
            print(error)
        print("Please fix the errors and try again.")
        return  # Exit the function if errors are found

    # Step 2: Tokenize the input code
    tokens = tokenize(code)

    # Step 3: Ask to display tokens
    print("\nDo you want to display the tokens? (yes/no)")
    choice = input().strip().lower()
    if choice == "yes":
        print("\nTokens:")
        for token in tokens:
            print(f"{token[0]:<15}: {token[1]}")

    compute_first()
    compute_follow()

    while True:
        print("\nMenu:")
        print("1. Display Token Table")
        print("2. Display Parse Table")
        print("3. Exit")
        choice = input("Enter your choice (1/2/3): ").strip()

        if choice == "1":
            token_table = create_token_table(tokens)
            print("\nToken Table:")
            for entry in token_table:
                print(f"{entry['Token Name']:<15} | {entry['Token Value']:<15} | {entry['Hash Value']}")
        elif choice == "2":
            parse_table = build_parse_table()
            print("\nParse Table:")
            for non_terminal, rules in parse_table.items():
                print(f"{non_terminal}: {rules}")
        elif choice == "3":
            print("Exiting the current code processing. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


def main():
    while True:
        print("Welcome to the Lexical Analyzer and Parser!")
        print("Enter your C++ code below. When you're done, type 'END' on a new line.")
        code_lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            code_lines.append(line)

        code = "\n".join(code_lines)

        process_code(code)

        print("\nDo you want to analyze another code? (yes/no)")
        continue_choice = input().strip().lower()
        if continue_choice != "yes":
            print("Exiting the program. Goodbye!")
            break


if __name__ == "__main__":
    main()
