import os
import json
import time
from groq import Groq
import sys
from main import generate_IEC_JSON, regenerate_IEC_JSON 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from backend.validator import validator

def generate_testcases():
    with open("generated_prompts.json","r") as f:
        prompts = json.load(f)
    
    for i, prompt in enumerate(prompts):
        errors = {}
        with open("testcases.json","a") as f:
            try:
                max_attempts = 5
                intermediate_code = generate_IEC_JSON(prompt)
                response = validator(json.loads(intermediate_code))
                while(response[0] == False and max_attempts>0):
                    max_attempts -= 1
                    print("Regenerating IEC JSON due to validation errors...")
                    print("Intermediate Code:", intermediate_code)
                    print(f"Errors: {response[1]}")
                    print("\n\n")
                    intermediate_code = regenerate_IEC_JSON(prompt,response[1],intermediate_code)
                    response = validator(json.loads(intermediate_code))
                if response[0] == True:
                    print("Conversion successful and validated!")
                    f.write(json.dumps({"instruction":prompt,"output":intermediate_code})+"\n")
                else:
                    print(f"Failed to generate valid IEC JSON after multiple attempts for prompt: {prompt}")
                    errors[prompt] = [response[1] , intermediate_code]
            except Exception as e:
                print(f"Error processing prompt: \nError: {e}")
                errors[prompt] = str(e)
            
            if errors:
                with open("errors.json","a") as error_file:
                    json.dump(errors, error_file, indent=2)
                    error_file.write("\n")


    

def generate_prompts_with_ai(client, num_to_generate, topic="IEC 61131 automation"):
    """
    Generates a list of unique and creative prompts using the Groq API.
    
    Args:
        client: An initialized Groq client object.
        num_to_generate (int): The total number of prompts to generate.
        topic (str): The specific topic for the prompts.
        
    Returns:
        list: A list of generated prompt strings.
    """
    system_prompt = (
        "You are an expert prompt generator for large language models. Your task is to create "
        "a list of highly specific, unique, and creative prompts for an AI model that translates "
        "industrial automation logic (like IEC 61131) into a JSON format. The prompts must "
        "represent complex, real-world scenarios and avoid simple, repetitive templates. "
        "Focus on diverse components, logic types (loops, conditionals), and function calls. "
        "Ensure each prompt is a complete, descriptive sentence or two, clearly outlining the desired logic."
    )

    # We will generate prompts in batches to avoid API limits.
    batch_size = 50 # Number of prompts per API call.
    total_prompts = []
    
    # Calculate the number of API calls needed.
    num_calls = (num_to_generate + batch_size - 1) // batch_size
    
    print(f"Starting to generate {num_to_generate} prompts in {num_calls} batches of {batch_size}...")

    for i in range(num_calls):
        user_prompt = (
            f"Generate {batch_size} unique and creative prompts based on the following topic: '{topic}'. "
            "The prompts should cover a variety of scenarios, including but not limited to: "
            "- Chemical mixing and batching processes (e.g., using a FOR loop to add ingredients).\n"
            "- Robotic arm or CNC machine control (e.g., using a WHILE loop for a repetitive task).\n"
            "- Smart building or HVAC systems (e.g., using a CASE statement for different operating modes).\n"
            "- Complex nested logic (e.g., an IF statement inside a FOR loop).\n"
            "- Function and Function Block definitions and calls (e.g., a TON timer controlling a motor).\n"
            "- Usage of arrays and custom data structures (STRUCTs).\n"
            "Return the prompts as a JSON array of strings, like this: "
            '["Prompt 1", "Prompt 2", "Prompt 3", ...]. Do not include any other text or explanation.'
            "Ensure the prompts are varied and do not repeat similar structures."
            "Numerical values can also be included in the prompt as it reflects real world scenarios"
        )
        
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama3-8b-8192",
                response_format={"type": "json_object"}
            )
            
            prompts_str = chat_completion.choices[0].message.content
            prompts_dict = json.loads(prompts_str)
            
            if isinstance(prompts_dict, list):
                total_prompts.extend(prompts_dict)
            else:
                # Assuming the JSON might be a dict with a "prompts" key
                total_prompts.extend(prompts_dict.get("prompts", []))

            print(f"Batch {i+1}/{num_calls} successful. Generated {len(total_prompts)} prompts so far.")
            
            # Add a delay to respect API rate limits.
            time.sleep(3) # Pauses for 3 seconds. Adjust if needed.

        except Exception as e:
            print(f"An error occurred during batch {i+1}: {e}")
            print("Retrying after a longer delay...")
            time.sleep(10) # Wait longer on error.
            # You might want to implement more sophisticated retry logic here.
    
    return total_prompts

def main():
    """
    Main function to initialize the client and generate prompts.
    """
    try:
        api_key = os.environ.get("GROQ_API_KEY")
       

        client = Groq(api_key=api_key)
        
        num_prompts_to_generate = 10000 
        
        generated_prompts = generate_prompts_with_ai(client, num_prompts_to_generate)
        
        if generated_prompts:
            print(f"\n--- Successfully Generated {len(generated_prompts)} Prompts ---")
            
            output_file = "generated_prompts.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(generated_prompts, f, indent=2)
            print(f"\nSaved prompts to {output_file}")
            
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

generate_testcases()